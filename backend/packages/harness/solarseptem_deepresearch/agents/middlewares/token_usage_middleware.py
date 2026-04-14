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
import logging
from typing import override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langgraph.runtime import Runtime

from solarseptem_deepresearch.utils import logger


class TokenUsageMiddleware(AgentMiddleware):
    """Logs token usage from model response usage_metadata."""

    @override
    def after_model(self, state: AgentState, runtime: Runtime) -> dict | None:
        return self._log_usage(state)

    @override
    async def aafter_model(self, state: AgentState, runtime: Runtime) -> dict | None:
        return self._log_usage(state)

    def _log_usage(self, state: AgentState) -> None:
        messages = state.get("messages", [])
        if not messages:
            return None
        last = messages[-1]
        usage = getattr(last, "usage_metadata", None)
        if usage:
            logger.info(
                "LLM token usage: input=%s output=%s total=%s",
                usage.get("input_tokens", "?"),
                usage.get("output_tokens", "?"),
                usage.get("total_tokens", "?"),
            )
        return None