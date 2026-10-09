import json
import sys

from rich import print

import app_instance

from hypercorn.asyncio import serve
from hypercorn.config import Config

import asyncio
import aiosqlite
from quart import jsonify, request

from app_instance import app
from endpoints.models import friendRequests, punishment, partyExpires, messages, gameStats, partyInvites, parties, users
from utils.config import quart_host, quart_port
from utils.deliveries import DeliveryService, deliver
from utils.errors import AuthenticationFailException, MissingHeadersException, DuplicateRequestException
from utils.tracking import preprocess_request, log_after_request
from utils.servers import Server
from utils.tasks import run_cache
from utils.commands import execute_command

from endpoints import cache, markoffline, seq

shutdown_event = asyncio.Event()

def get(key : str):
    with open("config.json", "r") as f:
        data = json.load(f)

        return data.get(key)

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
        print(f"[red]Authentication failed for the above request! Reason: {ex}[/red]")
        return jsonify({"error" : str(ex)}), 403

    except DuplicateRequestException as ex:
        return jsonify({"error": str(ex)}), 409

    return None

@app.after_request
async def after_request(response):
    await log_after_request(request, response)

    return response

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
        await deliver("users", [dict(row) for row in new_rows], [dict(row) for row in new_rows])

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

        if line == "":  # stdin closed
            shutdown_event.set()
            return

        line = line.rstrip("\r\n")

        try:
            await execute_command(line)
        except Exception as ex:
            print(f"[red]Command failed: {ex}[/red]")

app.register_blueprint(parties.party_blueprint)
app.register_blueprint(partyExpires.expire_blueprint)
app.register_blueprint(partyInvites.invite_blueprint)
app.register_blueprint(users.user_blueprint)
app.register_blueprint(punishment.punishment_blueprint)
app.register_blueprint(messages.message_blueprint)
app.register_blueprint(friendRequests.friend_request_blueprint)
app.register_blueprint(gameStats.game_stats_blueprint)

print(f"[green]Loaded blueprints:[/green] {list(app.blueprints.keys())}")

if __name__ == "__main__":
    config = Config()
    config.bind = [f"{quart_host}:{quart_port}"]

    config.accesslog = None

    try:
        asyncio.run(serve(app, config, shutdown_trigger = shutdown_event.wait))
    except KeyboardInterrupt:
        pass