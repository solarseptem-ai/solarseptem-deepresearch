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
"""Store provider for the DeerFlow runtime.

Re-exports the public API of both the async provider (for long-running
servers) and the sync provider (for CLI tools and the embedded client).

Async usage (FastAPI lifespan)::

    from solarseptem.runtime.store import make_store

    async with make_store() as store:
        app.state.store = store

Sync usage (CLI / DeerFlowClient)::

    from solarseptem.runtime.store import get_store, store_context

    store = get_store()                   # singleton
    with store_context() as store: ...    # one-shot
"""

from .async_provider import make_store
from .provider import get_store, reset_store, store_context

__all__ = [
    # async
    "make_store",
    # sync
    "get_store",
    "reset_store",
    "store_context",
]
