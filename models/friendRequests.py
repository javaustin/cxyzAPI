import aiosqlite
from quart import request, jsonify, Blueprint

import app_instance
from other.utils import deliver

print(f"loaded {__name__} routes")

friend_request_blueprint = Blueprint('friendRequest', __name__, url_prefix = "/friendRequest")

@friend_request_blueprint.route("/create", methods=["POST"])
async def create():
    data = await request.get_json()

    sender = data.get("sender")
    recipient = data.get("recipient")
    expire_timestamp = data.get("expireTimestamp")

    if not all([sender, recipient, expire_timestamp]):
        return jsonify({"error": "sender, recipient, expire_timestamp is required"}), 400

    try:
        db = app_instance.db

        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        operation = await db.execute("INSERT INTO friendRequests (sender, recipient, expireTimestamp) VALUES (?, ?, ?) RETURNING *", (sender, recipient, expire_timestamp,))

        after_rows = [dict(row) for row in await operation.fetchall()]

        await deliver("friendRequests", after_rows, [])

        await db.commit()

        return jsonify({"message": "Operation successful."}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error", str(ex)}), 500


@friend_request_blueprint.route("/delete", methods=["POST"])
async def delete():
    data = await request.get_json()

    sender = data.get("sender")
    recipient = data.get("recipient")

    try:
        db = app_instance.db

        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("DELETE FROM friendRequests WHERE sender = ? AND recipient = ? RETURNING *", (sender, recipient))

        await deliver("friendRequests", [], [dict(row) for row in await cursor.fetchall()])

        await db.commit()
        return jsonify({"message": "Operation successful."}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error", str(ex)}), 500

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= #
__all__ = ["friend_request_blueprint"]