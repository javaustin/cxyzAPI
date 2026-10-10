import aiosqlite
from quart import request, jsonify

import app_instance
from app_instance import app
from utils.deliveries import deliver
from utils.servers import Server


@app.route("/markOffline", methods = ["POST"])
async def mark_offline():
    data = await request.get_json()

    server = data.get("server")

    if server is None:
        return jsonify({"error" : "`server` is required."}), 400

    if Server.get_server(server) is None:
        return jsonify({"error" : f"Invalid server : {server}"}), 400

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