import json
import sys

from rich import print

from hypercorn.asyncio import serve
from hypercorn.config import Config

import asyncio
from quart import jsonify, request

from app_instance import app
from endpoints.models import friendRequests, punishment, partyExpires, messages, gameStats, partyInvites, parties, users
from utils.config import quart_host, quart_port
from utils.errors import AuthenticationFailException, MissingHeadersException, DuplicateRequestException
from utils.tracking import preprocess_request, log_after_request
from utils.commands import execute_command

# Do not delete this import
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

print(f"[white]Loaded blueprints: {list(app.blueprints.keys())}[/white]")

if __name__ == "__main__":
    config = Config()
    config.bind = [f"{quart_host}:{quart_port}"]

    config.accesslog = None

    try:
        asyncio.run(serve(app, config, shutdown_trigger = shutdown_event.wait))
    except KeyboardInterrupt:
        pass