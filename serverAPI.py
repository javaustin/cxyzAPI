import json

from models import messages, parties, partyInvites, partyExpires, punishment, users, friendRequests

import asyncio
import aiosqlite
from quart import jsonify, request

from app_instance import app
from other.servers import Server
from other.tasks import run_cache
from other.utils import path, deliver, api_key, DeliveryService


@app.before_request
async def authorize():
    key = request.headers.get("X-API-KEY")

    if key is None or key != api_key:
        return jsonify({"message" : "Unauthorized"}), 401

    return None

@app.route("/", methods=["GET"])
async def home():
    return "Hello world!"

@app.route("/cache", methods = ["POST"])
async def cache():

    if DeliveryService.is_delivering == True:
        return jsonify({"message" : "The request will not be fulfilled as a cache delivery is already in progress."}), 208

    data = await request.get_json()

    tables = data.get("tables")

    if not tables:
        tables = DeliveryService.tables
    else:
        tables = json.loads(tables)

    asyncio.create_task(run_cache(tables))

    return jsonify({"message" : "Operation successful"}), 200

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


@app.route("/seq/<table>", methods = ["GET"])
async def seq(table):

    if table is None:
        return jsonify({"error": "`table` is required."}), 400


    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(f"SELECT * FROM sqlite_sequence WHERE name = ?", (table,))

        res = await cursor.fetchone()

        if res is not None:
            return jsonify({"seq": int(res["seq"])}), 200

        else:
            return jsonify({"error": f"Table '{table}' does not exist!"}), 404


Server.load_servers()
Server.load_api()


app.register_blueprint(parties.party_blueprint)
app.register_blueprint(partyExpires.expire_blueprint)
app.register_blueprint(partyInvites.invite_blueprint)
app.register_blueprint(users.user_blueprint)
app.register_blueprint(punishment.punishment_blueprint)
app.register_blueprint(messages.message_blueprint)
app.register_blueprint(friendRequests.friend_request_blueprint)

if __name__ == "__main__":
    app.run(port = 5000, debug = True, use_reloader = False)