import base64
import hashlib
import hmac
import json
import httpx
import aiosqlite

from other.servers import Server


class DeliveryService:
    is_delivering = False
    tables = ["parties", "messages", "users", "punishments", "partyExpires", "partyInvites", "friendRequests"]


def get(key : str):
    with open("config.json", "r") as f:
        data = json.load(f)

        return data.get(key)

path = get("db-path")
api_key = get("api-key")

async def post_request(url : str, data : dict):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json = data, headers = {'content-type' : "application/json"}, timeout = 5.0)

            print(f"✅ POST request sent to {url} completed.")
            return None

    except Exception as ex:
        print(f"❌ POST request sent to {url} failed with an exception! {ex}")
        return None

async def ship(table : str = "users"):
    # Sends a json copy of an entire table to all game servers.
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(f"SELECT * FROM {table}")

        res = await cursor.fetchall()

        with open("config.json", "r") as f:
            data = json.load(f)

        for server in Server.servers:
            await post_request(f"{server.ip}/{table}Shipment", {"data" : [dict(row) for row in res]})

async def deliver(table : str, new_rows : list, old_rows : list):
    # Sends a json copy of any updated rows to all game servers.

    with open("config.json", "r") as f:
        data = json.load(f)

    for server in Server.servers:
        await post_request(
            f"{server.ip}/{table}Delivery",
            {
                "new_data": [row for row in new_rows],
                "old_data": [row for row in old_rows]
            }
        )

def generate_signature(identifier : str, secret : str, timestamp : int, method : str, path : str, payload_json : str):
    if payload_json is None:
        payload_json = ""

    message = identifier + "\n" + str(timestamp) + "\n" + method + "\n" + path + "\n" + payload_json

    mac = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256())

    signature = base64.b64encode(mac.digest())

    return signature


# def authenticate_request():
