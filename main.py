import json
import re
import sys

import app_instance
import other.utils
from models import messages, parties, partyInvites, partyExpires, punishment, users, friendRequests, gameStats

import asyncio
import aiosqlite
from quart import jsonify, request

from app_instance import app
from other.errors import AuthenticationFailException, MissingHeadersException, DuplicateRequestException
from other.servers import Server
from other.tasks import run_cache
from other.utils import preprocess_request, postprocess_request, DeliveryService, quart_host, quart_port

@app.route("/", methods=["GET", "POST"])
async def home():
    return jsonify({"message" : "Welcome to my web server!"})

@app.before_serving
async def startup():
    app.console_task = asyncio.create_task(console())

@app.before_request
async def preprocess():
    try:
        await preprocess_request(request)

    except MissingHeadersException as ex:
        return jsonify({"error": str(ex)}), 401

    except AuthenticationFailException as ex:
        print(f"Authentication failed for the above request! Reason: {ex}")
        return jsonify({"error" : str(ex)}), 403

    except DuplicateRequestException as ex:
        return jsonify({"error": str(ex)}), 409

    return None

@app.after_request
async def after_request(response):
    await postprocess_request(request, response)

    return response

@app.route("/sql", methods = ["POST"])
async def sql():
    data = await request.get_json()

    if not data:
        return jsonify({"error" : "No request body supplied."}), 400

    query = data.get("query")

    if not query:
        return jsonify({"error" : "`query` is required."}), 400

    try:
        db = app_instance.db

        async with app_instance.db_lock:
            cursor = await db.execute(query)
            rows = await cursor.fetchall()
            await cursor.close()
            await db.commit()

        match = re.search(
            r"(?:FROM|INTO|UPDATE)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            query,
            re.IGNORECASE
        )
        table = match.group(1) if match else None

        should_push : bool = query.upper().startswith("INSERT") or query.upper().startswith("UPDATE") or query.upper().startswith("DELETE") or query.upper().startswith("REPLACE")

        if table and should_push:
            await other.utils.deliver(table, [dict(row) for row in rows], [dict(row) for row in rows])

        elif not table:
            return jsonify({"error" : "Could not fulfill push because the SQL query does not include a table."}), 400

        res = [dict(row) for row in rows]

        return jsonify(res), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : ex.__str__()}), 400


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
        return jsonify({"error" : "`server` is required."}), 400

    if Server.get_server(server) is None:
        return jsonify({"error" : "Invalid server."}), 400

    try:
        db = app_instance.db

        async with app_instance.db_lock:
            cursor = await db.execute("UPDATE users SET online = false WHERE server = ? AND online = false RETURNING *", (server,))
            new_rows = await cursor.fetchall()
            await cursor.close()
            await db.commit()

        if len(new_rows) == 0:
            return jsonify({"message": "Operation successful!"}), 200

        # If we don't know exactly what kind of query we are receiving, we can simply provide the same rows.
        # The plugin will delete (by key) what we mark as old data, and put in new data. So in effect we just modified the data.
        await other.utils.deliver("users", [dict(row) for row in new_rows], [dict(row) for row in new_rows])

        if new_rows is None:
            return jsonify({"message": "Operation successful!"}), 200

        return jsonify([dict(row) for row in new_rows]), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 400

@app.route("/seq/<table>", methods = ["GET"])
async def seq(table):
    if table is None:
        return jsonify({"error" : "`table` is required."}), 400

    db = app_instance.db
    try:
        async with app_instance.db_lock:
            cursor = await db.execute(f"SELECT * FROM sqlite_sequence WHERE name = ?", (table,))
            res = await cursor.fetchone()
            await cursor.close()

        if res is not None:
            return jsonify({"seq": int(res["seq"])}), 200

        else:
            return jsonify({"seq": 0}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 400

async def console():

    while True:
        line = await asyncio.to_thread(sys.stdin.readline)

        if not line:
            return

        command = line.strip()

        print("Received command: " + command)


app.register_blueprint(parties.party_blueprint)
app.register_blueprint(partyExpires.expire_blueprint)
app.register_blueprint(partyInvites.invite_blueprint)
app.register_blueprint(users.user_blueprint)
app.register_blueprint(punishment.punishment_blueprint)
app.register_blueprint(messages.message_blueprint)
app.register_blueprint(friendRequests.friend_request_blueprint)
app.register_blueprint(gameStats.game_stats_blueprint)

if __name__ == "__main__":
    app.run(host = quart_host, port = quart_port, debug = False, use_reloader = False)
