import aiosqlite
from quart import request, jsonify, Blueprint

import app_instance
from other.utils import path, deliver

print(f"loaded {__name__} routes")

invite_blueprint = Blueprint('partyInvite', __name__, url_prefix = "/partyInvite")

@invite_blueprint.route("/create", methods=["POST"])
async def create():
    data = await request.get_json()

    inviter = data.get("inviter")
    recipient = data.get("recipient")
    expire_timestamp = data.get("expireTimestamp")

    db = app_instance.db

    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        after = await db.execute("INSERT INTO partyInvites (inviter, recipient, expireTimestamp) VALUES (?, ?, ?) RETURNING *", (inviter, recipient, expire_timestamp,))

        after_rows = [dict(row) for row in await after.fetchall()]

        await deliver("partyInvites", after_rows, [])

        await db.commit()

        return jsonify({"message": "Operation successful."}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error", str(ex)}), 500


@invite_blueprint.route("/sync", methods=["POST"])
async def sync():
    data = await request.get_json()

    inviter = data.get("inviter")
    recipient = data.get("recipient")
    expire_timestamp = data.get("expireTimestamp")

    db = app_instance.db

    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        after = await db.execute("UPDATE partyInvites SET inviter = ?, recipient = ?, expireTimestamp = ? WHERE inviter = ? RETURNING *", (inviter, recipient, expire_timestamp, inviter,))

        after_rows = [dict(row) for row in await after.fetchall()]

        await deliver("partyInvites", after_rows, [])

        await db.commit()

        return jsonify({"message": "Operation successful."}), 200


    except aiosqlite.OperationalError as ex:
        return jsonify({"error", str(ex)}), 500


@invite_blueprint.route("/delete", methods=["POST"])
async def delete():
    data = await request.get_json()

    inviter = data.get("inviter")
    recipient = data.get("recipient")

    db = app_instance.db

    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("DELETE FROM partyInvites WHERE inviter = ? AND recipient = ? RETURNING *", (inviter, recipient))

        await deliver("partyInvites", [], [dict(row) for row in await cursor.fetchall()])

        await db.commit()
        return jsonify({"message": "Operation successful."}), 200


    except aiosqlite.OperationalError as ex:
        return jsonify({"error", str(ex)}), 500


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= #
__all__ = ["invite_blueprint"]