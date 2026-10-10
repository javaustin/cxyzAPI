import asyncio
import json

from quart import request, jsonify, Blueprint

import app_instance
from app_instance import app
from utils.deliveries import DeliveryService
from utils.tasks import run_cache

@app.route("/cache", methods = ["POST"])
async def cache():
    data = await request.get_json()

    tables : list[str] = data.get("tables")

    if not tables:
        tables = DeliveryService.tables_to_deliver

    allowed_tables = []

    db = app_instance.db

    async with app_instance.db_lock:
        cursor = await db.execute(f"SELECT name FROM sqlite_master WHERE type='table' ORDER BY NAME")
        res = await cursor.fetchall()
        await cursor.close()

        allowed_tables = [dict(row).get("name") for row in res]

    for table in tables:
        if table not in allowed_tables:
            return jsonify({"error" : f"Invalid table: {table}"}), 400

    asyncio.create_task(run_cache(tables))

    return jsonify({"message" : "Operation successful"}), 200