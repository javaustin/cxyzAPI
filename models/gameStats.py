from quart import request, jsonify, Blueprint
import aiosqlite

import app_instance
from other.utils import deliver

print(f"loaded {__name__} routes")

game_stats_blueprint = Blueprint('gameStat', __name__, url_prefix ="/gameStat")

@game_stats_blueprint.route("/set", methods = ["POST"])
async def set():
    data = await request.get_json()

    uuid = data.get("uuid")
    stat_id = data.get("statID")
    value = data.get("value")
    version = data.get("version")

    try:
        version = int(version)
    except ValueError:
        return jsonify({"error": "`version` must be an integer"}), 400

    print("version: " + str(version))

    if not all([uuid, stat_id, value, version]):
        return jsonify({"error": "`uuid`, `statID`, `value`, and `version` are required arguments"}), 400

    db = app_instance.db

    try:
        async with app_instance.db_lock:
            before = await db.execute("SELECT * FROM gameStats WHERE uuid = ? AND statID = ?", (uuid, stat_id,))
            rows = await before.fetchall()
            await before.close()

            if len(rows) == 0:
                after = await db.execute(
                    f"INSERT INTO gameStats (uuid, statID, value, version) VALUES (?, ?, ?, ?) RETURNING *",
                    (uuid, stat_id, value, version,)
                )
            else:
                after = await db.execute(
                    f"UPDATE gameStats SET value = ?, version = ? WHERE uuid = ? AND statID = ? AND version < ? RETURNING *",
                    (value, version, uuid, stat_id, version,)
                )

            rows = [dict(row) for row in await after.fetchall()]
            await after.close()
            await db.commit()

        await deliver("gameStats", rows, [])

        return jsonify({"message": "Operation successful"}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 400


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= #
__all__ = ["game_stats_blueprint"]
