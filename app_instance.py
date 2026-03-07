from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart

app = Quart(__name__)

db = None

scheduler = AsyncIOScheduler()

print("Running app...")