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

from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from solarseptem_deepresearch.utils import logger


@dataclass
class SubagentConfig:
    """Configuration for a subagent.

    Attributes:
        name: Unique identifier for the subagent.
        description: When Claude should delegate to this subagent.
        system_prompt: The system prompt that guides the subagent's behavior.
        tools: Optional list of tool names to allow. If None, inherits all tools.
        disallowed_tools: Optional list of tool names to deny.
        model: Model to use - 'inherit' uses parent's model.
        max_turns: Maximum number of agent turns before stopping.
        timeout_seconds: Maximum execution time in seconds (default: 900 = 15 minutes).
    """

    name: str
    description: str
    system_prompt: str
    tools: list[str] | None = None
    disallowed_tools: list[str] | None = field(default_factory=lambda: ["task"])
    model: str = "inherit"
    max_turns: int = 50
    timeout_seconds: int = 900


class SubagentOverrideConfig(BaseModel):
    """Per-agent configuration overrides."""

    timeout_seconds: int | None = Field(
        default=None,
        ge=1,
        description="Timeout in seconds for this subagent (None = use global default)",
    )


class SubagentsAppConfig(BaseModel):
    """Configuration for the subagent system."""

    timeout_seconds: int = Field(
        default=900,
        ge=1,
        description="Default timeout in seconds for all subagents (default: 900 = 15 minutes)",
    )
    agents: dict[str, SubagentOverrideConfig] = Field(
        default_factory=dict,
        description="Per-agent configuration overrides keyed by agent name",
    )

    def get_timeout_for(self, agent_name: str) -> int:
        """Get the effective timeout for a specific agent.

        Args:
            agent_name: The name of the subagent.

        Returns:
            The timeout in seconds, using per-agent override if set, otherwise global default.
        """
        override = self.agents.get(agent_name)
        if override is not None and override.timeout_seconds is not None:
            return override.timeout_seconds
        return self.timeout_seconds


_subagents_config: SubagentsAppConfig = SubagentsAppConfig()


def get_subagents_app_config() -> SubagentsAppConfig:
    """Get the current subagents configuration."""
    return _subagents_config


def load_subagents_config_from_dict(config_dict: dict) -> None:
    """Load subagents configuration from a dictionary."""
    global _subagents_config
    _subagents_config = SubagentsAppConfig(**config_dict)

    overrides_summary = {name: f"{override.timeout_seconds}s" for name, override in _subagents_config.agents.items() if override.timeout_seconds is not None}
    if overrides_summary:
        logger.info(f"Subagents config loaded: default timeout={_subagents_config.timeout_seconds}s, per-agent overrides={overrides_summary}")
    else:
        logger.info(f"Subagents config loaded: default timeout={_subagents_config.timeout_seconds}s, no per-agent overrides")
