import aiosqlite
from quart import request, jsonify, Blueprint

import app_instance
from other.utils import path, deliver

print(f"loaded {__name__} routes")

expire_blueprint = Blueprint('partyExpire', __name__, url_prefix = "/partyExpire")

@expire_blueprint.route("/create", methods=["POST"])
async def create():
    data = await request.get_json()

    uuid = data.get("uuid")
    timestamp = data.get("timestamp")

    if not all([uuid, timestamp]):
        return jsonify({"error": "uuid, timestamp is required"}), 400

    db = app_instance.db

    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        before = await db.execute(f"SELECT * FROM users WHERE uuid = ?", (uuid,))

        if before.rowcount > 0:
            return jsonify({"error": "duplicate uuids"}), 400

        after = await db.execute("INSERT INTO partyExpires (uuid, timestamp) VALUES (?, ?) RETURNING *", (uuid, timestamp,))

        after_rows = [dict(row) for row in await after.fetchall()]

        await deliver("partyExpires", after_rows, [])

        await db.commit()

        return jsonify({"message": "Operation successful."}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error", str(ex)}), 500


@expire_blueprint.route("/sync", methods=["POST"])
async def sync():
    data = await request.get_json()

    uuid = data.get("uuid")
    timestamp = data.get("timestamp")

    if not all([uuid, timestamp]):
        return jsonify({"error": "uuid, timestamp is required"}), 400

    db = app_instance.db

    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        after = await db.execute("UPDATE partyExpires SET uuid = ?, timestamp = ? WHERE uuid = ? RETURNING *", (uuid, timestamp, uuid,))

        after_rows = [dict(row) for row in await after.fetchall()]

        await deliver("partyExpires", after_rows, [])

        await db.commit()

        return jsonify({"message": "Operation successful."}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error", str(ex)}), 500


@expire_blueprint.route("/delete", methods=["POST"])
async def delete():
    data = await request.get_json()

    uuid = data.get("uuid")

    db = app_instance.db

    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("DELETE FROM partyExpires WHERE uuid = ? RETURNING *", (uuid,))

        await deliver("partyExpires", [], [dict(row) for row in await cursor.fetchall()])

        await db.commit()

        return jsonify({"message": "Operation successful."}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error", str(ex)}), 500


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= #
__all__ = ["expire_blueprint"]