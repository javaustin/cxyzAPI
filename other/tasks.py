import asyncio
import datetime
import time

import aiosqlite

import app_instance
from app_instance import app, scheduler
from other.servers import Server
from other.utils import path, ship, deliver, DeliveryService

@app.before_serving
async def startup():
    Server.load_servers()
    Server.load_api()

    app_instance.db = await aiosqlite.connect(path)

    await run_cache(DeliveryService.tables) # Don't need a scheduler for this.

    scheduler.add_job(message_deleter, 'interval', minutes = 5)

    scheduler.add_job(party_invite_deleter, 'interval', minutes = 60)

    for job in scheduler.get_jobs():
        job.modify(next_run_time = datetime.datetime.now())

    scheduler.start()
    # Start the scheduler
    print("Task scheduler started")

async def run_cache(tables : list):
    if not tables:
        tables = DeliveryService.tables

    await asyncio.gather(*(ship(p) for p in tables))

async def message_deleter():
    """A task that removes any message with a timestamp older than 5 minutes."""

    db = app_instance.db

    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            f"DELETE FROM messages WHERE timestamp < ? RETURNING *",
            (int(time.time() - 300),)
        )

        new_rows = await cursor.fetchall()

        await db.commit()

        await deliver("messages", [], [dict(row) for row in new_rows])

    except aiosqlite.OperationalError as ex:
        print(f"message_deleter task error: {ex}")

async def party_invite_deleter():
    """A task that removes any PartyInvite with a timestamp lesser than unix time now."""

    db = app_instance.db

    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            f"DELETE FROM partyInvites WHERE expireTimestamp < ? RETURNING *",
            (int(time.time()),)
        )

        new_rows = await cursor.fetchall()

        await db.commit()

        await deliver("partyInvites", [], [dict(row) for row in new_rows])

    except aiosqlite.OperationalError as ex:
        print(f"party_invite_deleter task error: {ex}")
