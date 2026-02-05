import json
import httpx
import aiosqlite

def get_path():
    with open("config.json", "r") as f:
        data = json.load(f)

        return data.get("db-path")

path = get_path()

async def post_request(url : str, data : dict):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json = data, headers = {'content-type' : "application/json"})

            print(f"✅ POST request sent to {url} completed.")
            return None

    except Exception as ex:
        print(f"❌ POST request sent to {url} failed with an exception! {ex}")
        return None


async def is_authenticated(key):
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("SELECT * from apiKeys WHERE apiKey = ?", (key,))
        row = await cursor.fetchone()
        return row is not None


async def ship(table : str = "users"):
    # Sends a json copy of an entire table to all game servers.
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(f"SELECT * FROM {table}")

        res = await cursor.fetchall()

        with open("config.json", "r") as f:
            data = json.load(f)

        servers = data.get("servers", {})

        for name, ip in servers.items():
            await post_request(f"{ip}/{table}Shipment", {"data" : [dict(row) for row in res]})

async def deliver(table : str, new_rows : list, old_rows : list):
    # Sends a json copy of any updated rows to all game servers.

    with open("config.json", "r") as f:
        data = json.load(f)

    servers = data.get("servers", {})

    for name, ip in servers.items():
        await post_request(
            f"{ip}/{table}Delivery",
            {
                "new_data": [row for row in new_rows],
                "old_data": [row for row in old_rows]
            }
        )