from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils.servers import Server

# ^ The above code prevents registry.py from importing Server at runtime, but preserves type hints.

class ServerRegistry:
    servers: list[Server] = []
    api: Server
