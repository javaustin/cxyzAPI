import asyncio
import time

import aiosqlite

from app_instance import app, scheduler
from other.utils import path, ship, deliver, DeliveryService


@app.before_serving
async def startup():
    await run_cache(DeliveryService.tables) # Don't need a scheduler for this.
    # Start the scheduler

    await message_deleter() # This other library kind of sucks, so I have to call the task to run it at the top of the interval
    scheduler.add_job(message_deleter, 'interval', minutes = 5)

    await party_invite_deleter()
    scheduler.add_job(party_invite_deleter, 'interval', minutes = 60)

    scheduler.start()
    print("Task scheduler started")

async def run_cache(tables : list):
    await asyncio.gather(*(ship(p) for p in tables))


async def message_deleter():
    """A task that removes any message with a timestamp older than 5 minutes."""

    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            f"DELETE FROM messages WHERE timestamp < ? RETURNING *",
            (int(time.time() - 300),)
        )

        # if cursor.rowcount == 0:
        #     return

        new_rows = await cursor.fetchall()

        await db.commit()

        await deliver("messages", [], [dict(row) for row in new_rows])

async def party_invite_deleter():
    """A task that removes any PartyInvite with a timestamp lesser than unix time now."""

    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            f"DELETE FROM partyInvites WHERE expireTimestamp < ? RETURNING *",
            (int(time.time()),)
        )

        # if cursor.rowcount == 0:
        #     return

        new_rows = await cursor.fetchall()

        await db.commit()

        await deliver("partyInvites", [], [dict(row) for row in new_rows])
