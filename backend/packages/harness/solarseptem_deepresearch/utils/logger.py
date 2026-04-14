#  Copyright 2026 The sonhhxg0529 Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import json
import logging
import logging.handlers
import os
import sys
from collections import deque
from datetime import datetime
from pathlib import Path
from threading import Lock, Semaphore
from typing import Any, TypedDict

import orjson
import structlog
from platformdirs import user_cache_dir
from typing_extensions import NotRequired

SOLARSEPTEM_DEV = os.environ.get("SOLARSEPTEM_DEV", True)

VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Map log level names to integers
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class SizedLogBuffer:
    """用于存储日志消息供日志检索API使用的缓冲区"""

    def __init__(
            self,
            max_readers: int = 20,  # max number of concurrent readers for the buffer
    ):
        """Initialize the buffer.

        The buffer can be overwritten by an env variable LANGFLOW_LOG_RETRIEVER_BUFFER_SIZE
        because the logger is initialized before the settings_service are loaded.
        """
        self.buffer: deque = deque()

        self._max_readers = max_readers
        self._wlock = Lock()
        self._rsemaphore = Semaphore(max_readers)
        self._max = 0

    def get_write_lock(self) -> Lock:
        """Get the write lock."""
        return self._wlock

    def write(self, message: str) -> None:
        """Write a message to the buffer."""
        record = json.loads(message)
        log_entry = record.get("event", record.get("msg", record.get("text", "")))

        # Extract timestamp - support both direct timestamp and nested record.time.timestamp
        timestamp = record.get("timestamp", 0)
        if timestamp == 0 and "record" in record:
            # Support nested structure from tests: record.time.timestamp
            time_info = record["record"].get("time", {})
            timestamp = time_info.get("timestamp", 0)

        if isinstance(timestamp, str):
            # Parse ISO format timestamp
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            epoch = int(dt.timestamp() * 1000)
        else:
            epoch = int(timestamp * 1000)

        with self._wlock:
            if len(self.buffer) >= self.max:
                for _ in range(len(self.buffer) - self.max + 1):
                    self.buffer.popleft()
            self.buffer.append((epoch, log_entry))

    def __len__(self) -> int:
        """Get the length of the buffer."""
        return len(self.buffer)

    def get_after_timestamp(self, timestamp: int, lines: int = 5) -> dict[int, str]:
        """Get log entries after a timestamp."""
        rc = {}

        self._rsemaphore.acquire()
        try:
            with self._wlock:
                for ts, msg in self.buffer:
                    if lines == 0:
                        break
                    if ts >= timestamp and lines > 0:
                        rc[ts] = msg
                        lines -= 1
        finally:
            self._rsemaphore.release()

        return rc

    def get_before_timestamp(self, timestamp: int, lines: int = 5) -> dict[int, str]:
        """Get log entries before a timestamp."""
        self._rsemaphore.acquire()
        try:
            with self._wlock:
                as_list = list(self.buffer)
            max_index = -1
            for i, (ts, _) in enumerate(as_list):
                if ts >= timestamp:
                    max_index = i
                    break
            if max_index == -1:
                return self.get_last_n(lines)
            rc = {}
            start_from = max(max_index - lines, 0)
            for i, (ts, msg) in enumerate(as_list):
                if start_from <= i < max_index:
                    rc[ts] = msg
            return rc
        finally:
            self._rsemaphore.release()

    def get_last_n(self, last_idx: int) -> dict[int, str]:
        """Get the last n log entries."""
        self._rsemaphore.acquire()
        try:
            with self._wlock:
                as_list = list(self.buffer)
            return dict(as_list[-last_idx:])
        finally:
            self._rsemaphore.release()

    @property
    def max(self) -> int:
        """Get the maximum buffer size."""
        # Get it dynamically to allow for env variable changes
        if self._max == 0:
            env_buffer_size = os.getenv("SOLARSEPTEM_LOG_RETRIEVER_BUFFER_SIZE", "0")
            if env_buffer_size.isdigit():
                self._max = int(env_buffer_size)
        return self._max

    @max.setter
    def max(self, value: int) -> None:
        """Set the maximum buffer size."""
        self._max = value

    def enabled(self) -> bool:
        """Check if the buffer is enabled."""
        return self.max > 0

    def max_size(self) -> int:
        """Get the maximum buffer size."""
        return self.max


# 用于捕获日志消息的日志缓冲区
log_buffer = SizedLogBuffer()


def add_serialized(_logger: Any, _method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Add serialized version of the log entry."""
    # Only add serialized if we're in JSON mode (for log buffer)
    if log_buffer.enabled():
        subset = {
            "timestamp": event_dict.get("timestamp", 0),
            "message": event_dict.get("event", ""),
            "level": _method_name.upper(),
            "module": event_dict.get("module", ""),
        }
        event_dict["serialized"] = orjson.dumps(subset)
    return event_dict


def remove_exception_in_production(_logger: Any, _method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """删除生产中的异常详细信息。"""
    if SOLARSEPTEM_DEV is False:
        event_dict.pop("exception", None)
        event_dict.pop("exc_info", None)
    return event_dict


def buffer_writer(_logger: Any, _method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Write to log buffer if enabled."""
    if log_buffer.enabled() and "serialized" in event_dict:
        # Use the already-serialized version prepared by add_serialized()
        # This avoids duplicate serialization and ensures consistency
        serialized_bytes = event_dict["serialized"]
        log_buffer.write(serialized_bytes.decode("utf-8"))
    return event_dict


class LogConfig(TypedDict):
    """Configuration for logging."""

    log_level: NotRequired[str]
    log_file: NotRequired[Path]
    disable: NotRequired[bool]
    log_env: NotRequired[str]
    log_format: NotRequired[str]


# 配置日志记录器
def configure(
        *,
        log_level: str | None = None,
        log_file: Path | None = None,
        disable: bool | None = False,
        log_env: str | None = None,
        log_format: str | None = None,
        log_rotation: str | None = None,
        cache: bool | None = None,
        output_file=None,
) -> None:
    """Configure the logger."""
    # Early-exit only if structlog is configured AND current min level matches the requested one.
    cfg = structlog.get_config() if structlog.is_configured() else {}
    wrapper_class = cfg.get("wrapper_class")
    current_min_level = getattr(wrapper_class, "min_level", None)
    if os.getenv("SOLARSEPTEM_LOG_LEVEL", "").upper() in VALID_LOG_LEVELS and log_level is None:
        log_level = os.getenv("SOLARSEPTEM_LOG_LEVEL")

    log_level_str = os.getenv("SOLARSEPTEM_LOG_LEVEL", "ERROR")
    if log_level is not None:
        log_level_str = log_level

    requested_min_level = LOG_LEVEL_MAP.get(log_level_str.upper(), logging.ERROR)
    if current_min_level == requested_min_level:
        return

    if log_level is None:
        log_level = "ERROR"

    if log_file is None:
        env_log_file = os.getenv("SOLARSEPTEM_LOG_FILE", "")
        log_file = Path(env_log_file) if env_log_file else None

    if log_env is None:
        log_env = os.getenv("SOLARSEPTEM_LOG_ENV", "")

    # Get log format from env if not provided
    if log_format is None:
        log_format = os.getenv("SOLARSEPTEM_LOG_FORMAT")

    # 根据环境配置处理器
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="[%Y-%m-%d %H:%M:%S]"),
    ]

    # 添加呼叫站点信息，确保在所有环境中都能获取文件名和行号
    processors.append(
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        )
    )

    processors.extend(
        [
            add_serialized,
            remove_exception_in_production,
            buffer_writer,
        ]
    )

    # Configure output based on environment
    if log_env.lower() == "container" or log_env.lower() == "container_json":
        processors.append(structlog.processors.JSONRenderer())
    elif log_env.lower() == "container_csv":
        # Include callsite fields in key order when DEV is enabled
        key_order = ["timestamp", "level", "event"]
        key_order += ["filename", "lineno"]
        processors.append(structlog.processors.KeyValueRenderer(key_order=key_order, drop_missing=True))
    else:
        # 检查是否使用文件日志
        if log_file:
            # 文件日志模式：使用普通格式，不添加颜色
            def custom_file_formatter(logger, method_name, event_dict):
                # 提取字段
                ts = event_dict.get("timestamp", "")
                level = event_dict.get("level", "").upper()
                filename = event_dict.get("filename", "unknown")
                line = event_dict.get("lineno", 0)
                msg = event_dict.get("event", "")

                # 构建自定义格式的消息
                formatted_message = f"{ts} [{level}] [{filename}:{line}] | {msg}"
                return formatted_message

            processors.append(custom_file_formatter)
        else:
            # 控制台日志模式：使用彩色输出
            log_stdout_pretty = os.getenv("SOLARSEPTEM_PRETTY_LOGS", "true").lower() == "true"

            if log_stdout_pretty:
                # 自定义处理器，构建完整的日志消息并移除多余字段
                def custom_formatter(logger, method_name, event_dict):
                    # 提取字段
                    ts = event_dict.get("timestamp", "")
                    level = event_dict.get("level", "").upper()
                    filename = event_dict.get("filename", "unknown")
                    line = event_dict.get("lineno", 0)
                    msg = event_dict.get("event", "")

                    # 构建自定义格式的消息
                    formatted_message = f"{ts} [{filename}:{line}] | {msg}"

                    # 只保留必要的字段：event用于显示，level用于颜色
                    return {
                        "event": formatted_message,
                        "level": event_dict.get("level")
                    }

                processors.append(custom_formatter)
                # 使用默认的ConsoleRenderer，它会根据level字段应用颜色
                processors.append(structlog.dev.ConsoleRenderer(colors=True))
            else:
                # 非彩色模式使用普通输出
                def custom_format_log(_, __, event_dict):
                    # 提取字段
                    ts = event_dict.pop("timestamp", "")
                    level = event_dict.pop("level", "").upper()
                    filename = event_dict.pop("filename", "unknown")
                    line = event_dict.pop("lineno", 0)
                    msg = event_dict.pop("event", "")

                    # 拼接成要求的格式
                    return f"[{ts}] [{level}] [{filename}:{line}] | {msg}"

                processors.append(custom_format_log)

    # Get numeric log level
    numeric_level = LOG_LEVEL_MAP.get(log_level.upper(), logging.ERROR)

    # Create wrapper class and attach the min level for later comparison
    wrapper_class = structlog.make_filtering_bound_logger(numeric_level)
    wrapper_class.min_level = numeric_level

    # Configure structlog
    # Default to stdout for backward compatibility, unless output_file is specified
    log_output_file = output_file if output_file is not None else sys.stdout

    structlog.configure(
        processors=processors,
        wrapper_class=wrapper_class,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=log_output_file)
        if not log_file
        else structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=cache if cache is not None else True,
    )

    # Set up file logging if needed
    if log_file:
        if not log_file.parent.exists():
            cache_dir = Path(user_cache_dir("solarseptem"))
            log_file = cache_dir / "solarseptem.log"

        # Parse rotation settings
        if log_rotation:
            # Handle rotation like "1 day", "100 MB", etc.
            max_bytes = 10 * 1024 * 1024  # Default 10MB
            if "MB" in log_rotation.upper():
                try:
                    # Look for pattern like "100 MB" (with space)
                    parts = log_rotation.split()
                    expected_parts = 2
                    if len(parts) >= expected_parts and parts[1].upper() == "MB":
                        mb = int(parts[0])
                        if mb > 0:  # Only use valid positive values
                            max_bytes = mb * 1024 * 1024
                except (ValueError, IndexError):
                    pass
        else:
            max_bytes = 10 * 1024 * 1024  # Default 10MB

        # 由于structlog没有内置旋转，我们将使用stdlib日志记录文件输出
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=5,
        )
        file_handler.setFormatter(logging.Formatter("%(message)s"))

        # Add file handler to root logger
        logging.root.addHandler(file_handler)
        logging.root.setLevel(numeric_level)

    # Set up interceptors for uvicorn and gunicorn
    setup_uvicorn_logger()
    setup_gunicorn_logger()

    # Create the global logger instance
    global logger  # noqa: PLW0603
    logger = structlog.get_logger()

    if disable:
        # In structlog, we can set a very high filter level to effectively disable logging
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        )

    logger.debug("Logger set up with log level: %s", log_level)


def setup_uvicorn_logger() -> None:
    """Redirect uvicorn logs through structlog."""
    loggers = (logging.getLogger(name) for name in logging.root.manager.loggerDict if name.startswith("uvicorn."))
    for uvicorn_logger in loggers:
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True


def setup_gunicorn_logger() -> None:
    """Redirect gunicorn logs through structlog."""
    logging.getLogger("gunicorn.error").handlers = []
    logging.getLogger("gunicorn.error").propagate = True
    logging.getLogger("gunicorn.access").handlers = []
    logging.getLogger("gunicorn.access").propagate = True


class InterceptHandler(logging.Handler):
    """Intercept standard logging messages and route them to structlog."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record by passing it to structlog."""
        # Get corresponding structlog logger
        logger_name = record.name
        structlog_logger = structlog.get_logger(logger_name)

        # Map log levels
        level = record.levelno
        if level >= logging.CRITICAL:
            structlog_logger.critical(record.getMessage())
        elif level >= logging.ERROR:
            structlog_logger.error(record.getMessage())
        elif level >= logging.WARNING:
            structlog_logger.warning(record.getMessage())
        elif level >= logging.INFO:
            structlog_logger.info(record.getMessage())
        else:
            structlog_logger.debug(record.getMessage())


# 初始化记录器-调用configure（）时将重新配置
# Set it to critical level
logger: structlog.BoundLogger = structlog.get_logger()

configure(log_level="CRITICAL", cache=False, disable=True, log_rotation="100 MB")
