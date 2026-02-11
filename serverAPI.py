import random
import time

from models import messages, parties, partyInvites, partyExpires, punishment, users, friendRequests

import asyncio
import aiosqlite  # Importing aiosqlite for async database access
from quart import jsonify, request

from app_instance import app
from tasks.tasks import run_cache
from utils import path, deliver, is_authenticated


@app.before_request
async def authorize():
    key = request.headers.get("X-API-KEY")
    timestamp_millis = request.headers.get("X-Request-Expires")


    if key is None or not await is_authenticated(key):
        return jsonify({"message" : "Unauthorized"}), 401

    if timestamp_millis is not None:
        current_millis = time.time_ns() / 1_000_000

        if current_millis > float(timestamp_millis):
            # Request expired, prompt the server to send it again.
            return jsonify({"message" : "The request was received after the allowed time window provided and was not processed. Please try again!"}), 408

    return None

@app.route("/", methods=["GET"])
async def home():
    return "Hello world!"

@app.route("/cache", methods = ["POST"])
async def cache():
    asyncio.create_task(run_cache())
    return jsonify({"message" : "Operation successful"}), 200

@app.route("/generate_key", methods=["POST"])
async def generate_key():
    key = "".join(random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890") for _ in range(16))

    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.cursor()
        await cursor.execute("INSERT INTO apiKeys (apiKey, timestamp) VALUES (?, ?)", (key, time.time().__floor__()))
        await db.commit()

    return jsonify({"key": key}), 200

@app.route("/sql", methods=["POST"])
async def sql():
    # In practice, these are write only functions.

    data = await request.get_json()
    query = data.get("query")
    table = data.get("table")

    if not data or not table:
        return jsonify({"error": "`data` and `table` are required."}), 400  # bad request

    try:
        async with aiosqlite.connect(path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            db.row_factory = aiosqlite.Row

            operation = await db.execute(query)
            new_rows = await operation.fetchall()


            if operation.rowcount == 0:
                return jsonify({"message": "Operation successful!"}), 200

            # If we don't know exactly what kind of query we are receiving, we can simply provide the same rows. The plugin will delete (by key) what we mark as old data, and put in new data. So in effect we just modified the data.
            await deliver(table, [dict(row) for row in new_rows], [dict(row) for row in new_rows])

            await db.commit()

        if new_rows is None:
            return jsonify({"message": "Operation successful!"}), 200

        return jsonify([dict(row) for row in new_rows]), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error": str (ex)}), 500

app.register_blueprint(parties.party_blueprint)
app.register_blueprint(partyExpires.expire_blueprint)
app.register_blueprint(partyInvites.invite_blueprint)
app.register_blueprint(users.user_blueprint)
app.register_blueprint(punishment.punishment_blueprint)
app.register_blueprint(messages.message_blueprint)
app.register_blueprint(friendRequests.friend_request_blueprint)
print(app.url_map)

if __name__ == "__main__":
    app.run(port = 5000, debug = True, use_reloader = False)