import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart

app = Quart(__name__)

db = None
db_lock = asyncio.Lock()

scheduler = AsyncIOScheduler()

print("Running app...")
