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
from langgraph.graph import StateGraph

from solarseptem_deepresearch.core.prompt_enhancer.graph.enhancer_node import prompt_enhancer_node
from solarseptem_deepresearch.core.prompt_enhancer.graph.state import PromptEnhancerState


def build_graph():
    """Build and return the prompt enhancer workflow graph."""
    # Build state graph
    builder = StateGraph(PromptEnhancerState)

    # Add the enhancer node
    builder.add_node("enhancer", prompt_enhancer_node)

    # Set entry point
    builder.set_entry_point("enhancer")

    # Set finish point
    builder.set_finish_point("enhancer")

    # Compile and return the graph
    return builder.compile()