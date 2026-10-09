import asyncio
import json

from quart import request, jsonify, Blueprint

from app_instance import app
from utils.deliveries import DeliveryService
from utils.tasks import run_cache

@app.route("/cache", methods = ["POST"])
async def cache():
    data = await request.get_json()

    tables = data.get("tables")

    if not tables:
        tables = DeliveryService.tables_to_deliver

    asyncio.create_task(run_cache(tables))

    return jsonify({"message" : "Operation successful"}), 200