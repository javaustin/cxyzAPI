import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart

from rich import print

app = Quart(__name__)

db = None
db_lock = asyncio.Lock()

scheduler = AsyncIOScheduler()

print("[cyan]Starting app...[/cyan]")
