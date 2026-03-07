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
    gameID = data.get("gameID")
    statID = data.get("statID")
    value = data.get("value")
    version = data.get("version")

    print(data)

    try:
        version = int(version)
    except ValueError:
        return jsonify({"error" : "version must be an integer"}), 400

    print("version: " + str(version))

    if not all([uuid, gameID, statID, value, version]):
        return jsonify({"error": "uuid, gameID, statID, value, version are required"}), 400

    db = app_instance.db

    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        existing = await db.execute("SELECT * FROM gameStats WHERE uuid = ? AND gameID = ? AND statID = ?", (uuid, gameID, statID,))

        rows = await existing.fetchall()

        if len(rows) == 0:
            operation = await db.execute(
                f"INSERT INTO gameStats (uuid, gameID, statID, value, version) VALUES (?, ?, ?, ?, ?) RETURNING *",
                (uuid, gameID, statID, value, version,)
            )

        else:
            operation = await db.execute(
                f"UPDATE gameStats SET value = ?, version = ? WHERE uuid = ? AND gameID = ? AND statID = ? AND version < ? RETURNING *",
                (value, version, uuid, gameID, statID, version,)
            )

        rows = [dict(row) for row in await operation.fetchall()]

        await deliver("gameStats", rows, [])

        await db.commit()
        return jsonify({"message" : "Operation successful."}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 500


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= #
__all__ = ["game_stats_blueprint"]