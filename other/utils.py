import base64
import hashlib
import hmac
import json
import time
from urllib.parse import urlparse

import httpx
import aiosqlite
import quart.app

import app_instance
from other.errors import AuthenticationFailException
from other.servers import Server


class DeliveryService:
    is_delivering = False
    tables = ["parties", "messages", "users", "punishments", "partyExpires", "partyInvites", "friendRequests", "gameStats"]


def get(key : str):
    with open("config.json", "r") as f:
        data = json.load(f)

        return data.get(key)

path = get("db-path")
api_key = get("api-key")

async def post_request(url : str, data : dict):
    try:
        async with httpx.AsyncClient() as client:
            identifier : str = Server.api.identifier
            secret : str = Server.api.secret
            timestamp : int = int(time.time())

            urlpath : str = urlparse(url).path

            payload = json.dumps(data, separators=(',', ':'))

            signature = generate_signature(identifier = identifier, secret = secret, timestamp = timestamp, method = "POST", urlpath = urlpath, payload_json = payload)

            print(f"[🔃] POST in progress: {url}")
            result = await client.post(url, json = data, headers =
                    {
                    'content-type' : "application/json",
                    'X-Identifier' : Server.api.identifier,
                    'X-Timestamp' : str(timestamp),
                    'X-Signature' : signature
                    },
                              timeout = 5.0
                              )


            if result.status_code != 200:
                print(f"[⚠️] POST COMPLETED ({result.status_code}) {url}.\n\tBody: {json.dumps(result.json(), separators=(',', ':'))}")

            if result.status_code == 200:
                print(f"[✅] POST COMPLETED ({result.status_code}) {url}.\n\tBody: {json.dumps(result.json(), separators=(',', ':'))}")


            return None

    except Exception as ex:
        print(f"[❌] POST FAILED {url}.\n\t{ex}")
        return None

async def ship(table : str = "users"):
    # Sends a json copy of an entire table to all game servers.

    db = app_instance.db

    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(f"SELECT * FROM {table}")

        res = await cursor.fetchall()

        for server in Server.servers:
            await post_request(f"{server.ip}/{table}Shipment", {"data" : [dict(row) for row in res]})

    except Exception as ex:
        print(f"ship exception: {ex}")

async def deliver(table : str, new_rows : list, old_rows : list):
    # Sends a json copy of any updated rows to all game servers.

    new_data = [dict(row) for row in new_rows]
    old_data = [dict(row) for row in old_rows]

    if len(new_data) == 0 and len(old_data) == 0:
        return None

    for server in Server.servers:
        await post_request(
            f"{server.ip}/{table}Delivery",
            {
                "new_data": new_data,
                "old_data": old_data
            }
        )

    return None

def generate_signature(identifier : str, secret : str, timestamp : int, method : str, urlpath : str, payload_json : str):
    if payload_json is None:
        payload_json = ""

    message = identifier + " | " + str(timestamp) + " | " + method + " | " + urlpath + " | " + payload_json

    mac = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256)

    signature = base64.b64encode(mac.digest()).decode('utf-8')

    return signature


async def authenticate_request(request : quart.app.Request):

    data = await request.get_data(as_text = True)

    payload : str = data
    identifier : str = request.headers.get("X-Identifier", None)
    timestamp_string : str = request.headers.get("X-Timestamp", None)
    signature : str = request.headers.get("X-Signature", None)
    urlpath : str = request.path
    method : str = request.method

    if identifier is None:
        raise AuthenticationFailException("\"X-Identifier\" is required for interacting with this service.")

    if timestamp_string is None:
        raise AuthenticationFailException("\"X-Timestamp\" is required for interacting with this service.")

    if signature is None:
        raise AuthenticationFailException("\"X-Signature\" is required for interacting with this service.")

    try:
        provided_timestamp : int = int(timestamp_string)

    except Exception:
        raise AuthenticationFailException("Timestamp is invalid.")


    if (abs(time.time()) - abs(provided_timestamp)) > 30:
        raise AuthenticationFailException("Request timestamp expired.")

    server = Server.get_server(identifier)

    if server is None:
        raise AuthenticationFailException(f"No service with identifier={identifier} is registered.")

    local_signature = generate_signature(
        identifier = server.identifier,
        secret = server.secret,
        timestamp = provided_timestamp,
        method = method,
        urlpath = urlpath,
        payload_json = payload
    )

    if not hmac.compare_digest(signature, local_signature):
        raise AuthenticationFailException("Signature is invalid.")


    return None
