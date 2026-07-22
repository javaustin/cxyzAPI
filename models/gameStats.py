from quart import request, jsonify, Blueprint
import aiosqlite

import app_instance
from other.utils import deliver

print(f"loaded {__name__} routes")

game_stats_blueprint = Blueprint('gameStats', __name__, url_prefix ="/gameStat")

@game_stats_blueprint.route("/set", methods = ["POST"])
async def set():
    data = await request.get_json()

    uuid = data.get("uuid")
    stat_id = data.get("statID")
    value = data.get("value")
    version = data.get("version")

    print(data)

    try:
        version = int(version)
    except ValueError:
        return jsonify({"error" : "version must be an integer"}), 400

    print("version: " + str(version))

    if not all([uuid, stat_id, value, version]):
        return jsonify({"error" : "uuid,  statID, value, version are required"}), 400

    db = app_instance.db

    try:
        before = await db.execute("SELECT * FROM gameStats WHERE uuid = ? AND statID = ?", (uuid, stat_id,))

        rows = await before.fetchall()

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

        await deliver("gameStats", rows, [])


        await before.close()
        await after.close()

        await db.commit()

        return jsonify({"message" : "Operation successful."}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 500


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= #
__all__ = ["game_stats_blueprint"]
