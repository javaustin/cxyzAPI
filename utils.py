import json
import httpx
import aiosqlite

path = "C:/Users/Austin/Documents/serverAPI/server.db"

async def post_request(url : str, data : dict):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json = data, headers = {'content-type' : "application/json"})

            print(f"✅ POST request sent to {url} completed.")
            return None

    except Exception as ex:
        print(f"❌ POST request sent to {url} failed with an exception! {ex}")
        return None


# user info of a single user
async def get_user(uuid):  # user info of a single user
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("SELECT * FROM users WHERE uuid = ?", (uuid,))
        row = await cursor.fetchone()

    if row is None:
        return {"error": "UUID not found"}, 404
        # This is an error because a UUID cannot simply be misspelt by a player. It is only in code.

    return dict(row), 200

async def get_user_by_username(username):  # user info of a single user
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = await cursor.fetchone()

    if row is None:
        return {"message": "Player not found!"}, 404

    return dict(row), 200

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

        with open("servers.json", "r") as f:
            data = json.load(f)

        servers = data.get("servers", {})

        for name, ip in servers.items():
            await post_request(f"{ip}/{table}Shipment", {"data" : [dict(row) for row in res]})

async def deliver(table : str, new_rows : list, old_rows : list):
    # Sends a json copy of any updated rows to all game servers.

    with open("servers.json", "r") as f:
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