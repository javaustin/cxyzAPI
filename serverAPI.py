import json
import time

import app_instance
import other.utils
from models import messages, parties, partyInvites, partyExpires, punishment, users, friendRequests, gameStats

import asyncio
import aiosqlite
from quart import jsonify, request

from app_instance import app
from other.errors import AuthenticationFailException
from other.servers import Server
from other.tasks import run_cache
from other.utils import authenticate_request, DeliveryService

@app.before_request
async def authorize():
    try:
        await authenticate_request(request)

    except AuthenticationFailException as ex:
        return jsonify({"error" : str(ex)}), 401

    return None

@app.route("/", methods=["GET"])
async def home():
    return "Hello world!"

@app.route("/cache", methods = ["POST"])
async def cache():

    data = await request.get_json()

    tables = data.get("tables")

    if not tables:
        tables = DeliveryService.tables
    else:
        tables = json.loads(tables)

    asyncio.create_task(run_cache(tables))

    return jsonify({"message" : "Operation successful"}), 200

@app.route("/markOffline", methods = ["POST"])
async def mark_offline():
    data = await request.get_json()

    server = data.get("server")

    if server is None:
        return jsonify({"error", "`server` is required."}), 400

    if Server.get_server(server) is None:
        return jsonify({"error", "Invalid server."}), 400

    try:
        db = app_instance.db

        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        operation = await db.execute("UPDATE users SET online = false WHERE server = ?", (server,))
        new_rows = await operation.fetchall()

        if len(new_rows) == 0:
            return jsonify({"message": "Operation successful!"}), 200

        # If we don't know exactly what kind of query we are receiving, we can simply provide the same rows. The plugin will delete (by key) what we mark as old data, and put in new data. So in effect we just modified the data.
        await other.utils.deliver("users", [dict(row) for row in new_rows], [dict(row) for row in new_rows])

        await db.commit()

        if new_rows is None:
            return jsonify({"message": "Operation successful!"}), 200

        return jsonify([dict(row) for row in new_rows]), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error", str(ex)}), 500

@app.route("/seq/<table>", methods = ["GET"])
async def seq(table):
    start_time = time.time()

    if table is None:
        return jsonify({"error" : "`table` is required."}), 400


    db = app_instance.db
    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(f"SELECT * FROM sqlite_sequence WHERE name = ?", (table,))

        res = await cursor.fetchone()

        if res is not None:
            end_time = time.time()
            print(f"duration: {end_time - start_time}")

            return jsonify({"seq": int(res["seq"])}), 200

        else:
            end_time = time.time()
            print(f"duration: {end_time - start_time}")

            return jsonify({"seq": 0}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error", str(ex)}), 500




app.register_blueprint(parties.party_blueprint)
app.register_blueprint(partyExpires.expire_blueprint)
app.register_blueprint(partyInvites.invite_blueprint)
app.register_blueprint(users.user_blueprint)
app.register_blueprint(punishment.punishment_blueprint)
app.register_blueprint(messages.message_blueprint)
app.register_blueprint(friendRequests.friend_request_blueprint)
app.register_blueprint(gameStats.game_stats_blueprint)

if __name__ == "__main__":
    app.run(port = 5000, debug = False, use_reloader = False)