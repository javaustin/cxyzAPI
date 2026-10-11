import asyncio
import json
from typing import Any

from quart import request, jsonify

from app_instance import app
from utils.registry import ServerRegistry
from utils.requests import post_request


@app.route("/send_message", methods=["POST"])
async def send_message():
    og_data = await request.get_json()

    print(og_data)
    print(type(og_data))

    api_server = ServerRegistry.api
    results = []

    for game_server in ServerRegistry.servers:
        if game_server.identifier == api_server.identifier:
            continue

        print("Attempting to POST to " + game_server.ip + f"/send_message with data: {og_data}")

        body, status = await post_request(
            game_server.ip + "/send_message",
            og_data,
        )

        results.append({
            "server": game_server.identifier,
            "status": status,
            "body": body,
        })


    failed = any(status is None or (status < 200 or status >= 300) for status in (r["status"] for r in results))

    any_response = any(status is not None for status in (r["status"] for r in results))

    json_response : dict = {"results" : results}

    if not any_response:
        json_response["message"] = "Could not connect to any game servers!"

    return jsonify(json_response), (200 if not failed else 400 if any_response else 502)