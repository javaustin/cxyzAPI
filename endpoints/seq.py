import aiosqlite
from quart import jsonify

import app_instance
from app_instance import app


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