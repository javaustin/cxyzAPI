import asyncio
import datetime
import pathlib
import time

import aiosqlite

import app_instance
from app_instance import app, scheduler
from utils.config import path
from utils.deliveries import DeliveryService, ship, deliver
from utils.servers import Server

@app.before_serving
async def startup():
    Server.load_servers()
    Server.load_api()

    if pathlib.Path(path).exists():
        app_instance.db = await aiosqlite.connect(path)

    else:
        print(f"No database found at {path}. Creating...")

        await create_database(path)

    app_instance.db.row_factory = aiosqlite.Row
    cursor = await app_instance.db.execute("PRAGMA journal_mode=WAL")
    await app_instance.db.execute("PRAGMA busy_timeout = 5000")

    await cursor.close()

    cur_schema_version = 0

    db = app_instance.db

    async with app_instance.db_lock:
        # Older databases predate schema tracking; treat them as the baseline.
        await db.execute(
            "CREATE TABLE IF NOT EXISTS schema_version "
            "(key TEXT, value INTEGER NOT NULL)"
        )
        await db.execute(
            "INSERT INTO schema_version (key, value) "
            "SELECT ?, ? WHERE NOT EXISTS "
            "(SELECT 1 FROM schema_version WHERE key = ?)",
            ("version", 0, "version"),
        )
        await db.commit()

        cursor = await db.execute("SELECT value FROM schema_version WHERE key = ?", ("version",))
        res = await cursor.fetchone()
        await cursor.close()

        if res is None:
            raise RuntimeError("The database does not contain a schema version")

        cur_schema_version = int(res["value"])

    await apply_migrations(cur_schema_version)

    await run_cache(DeliveryService.tables_to_deliver) # Don't need a scheduler for this.

    scheduler.add_job(message_deleter, 'interval', minutes = 5)

    scheduler.add_job(party_invite_deleter, 'interval', minutes = 6)

    scheduler.add_job(checkpoint, 'interval', minutes = 30)


    for job in scheduler.get_jobs():
        job.modify(next_run_time = datetime.datetime.now())

    scheduler.start()
    # Start the scheduler
    print("Task scheduler started")

async def checkpoint():
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA busy_timeout = 5000")
        cursor = await db.execute("PRAGMA wal_checkpoint(TRUNCATE)")

        await cursor.close()



async def run_cache(tables : list):
    if not tables:
        tables = DeliveryService.tables_to_deliver

    await asyncio.gather(*(ship(p) for p in tables))

async def message_deleter():
    """A task that removes any message with a timestamp older than 5 minutes."""

    db = app_instance.db

    async with app_instance.db_lock:
        cursor = await db.execute(
            f"DELETE FROM messages WHERE timestamp < ? RETURNING *",
            (int(time.time() - 300),)
        )
        new_rows = await cursor.fetchall()
        await cursor.close()
        await db.commit()

    await deliver("messages", [], [dict(row) for row in new_rows])

async def party_invite_deleter():
    """A task that removes any PartyInvite with a timestamp lesser than unix time now."""

    db = app_instance.db

    async with app_instance.db_lock:
        cursor = await db.execute(
            f"DELETE FROM partyInvites WHERE expireTimestamp < ? RETURNING *",
            (int(time.time()),)
        )
        new_rows = await cursor.fetchall()
        await cursor.close()
        await db.commit()

    await deliver("partyInvites", [], [dict(row) for row in new_rows])

async def create_database(db_path : str):
    with open(db_path, "x"):
        pass

    app_instance.db = await aiosqlite.connect(db_path)

    schema_file = pathlib.Path(__file__).resolve().parent.parent / "migrations" / "schema.sql"

    with schema_file.open(encoding="utf8") as file:
        query = file.read()

        await apply_query(query)
        print(f"Applied initial schema '{file.name}'")

async def apply_migrations(start: int):
    folder = pathlib.Path(__file__).resolve().parent.parent / "migrations"
    files = []

    for item in folder.iterdir():
        if not item.is_file() or not item.name.endswith(".sql") or item.name == "schema.sql":
            continue

        try:
            number = int(item.name.split("_", 1)[0])
        except (ValueError, IndexError) as ex:
            raise ValueError(f"Migration filename must start with a number: {item.name}") from ex

        files.append((number, item))

    files.sort(key=lambda migration: migration[0])

    migration_numbers = [number for number, _ in files]
    if len(migration_numbers) != len(set(migration_numbers)):
        raise ValueError("Migration filenames must have unique version numbers")

    for number, file in files:
        # The stored version is the last migration already applied.
        if number <= start:
            continue

        with file.open(encoding="utf8") as sql_file:
            query = sql_file.read()

        await apply_query(query, number)
        print(f"Applied migration '{file.name}'")


async def apply_query(query : str, version: int | None = None):
    db = app_instance.db

    async with app_instance.db_lock:
        if version is not None:
            # Keep the schema change and its version marker in one transaction.
            query = (
                "BEGIN;\n"
                f"{query}\n"
                "UPDATE schema_version SET value = "
                f"{version} WHERE key = 'version';\n"
                "COMMIT;"
            )

        try:
            cursor = await db.executescript(query)
        except Exception:
            if version is not None:
                await db.rollback()
            raise

        await cursor.close()
        if version is None:
            await db.commit()
