import aiosqlite
from quart import request, jsonify, Blueprint

from other.utils import path, deliver

print(f"loaded {__name__} routes")

friend_request_blueprint = Blueprint('friendRequest', __name__, url_prefix = "/friendRequest")

@friend_request_blueprint.route("/create", methods=["POST"])
async def create():
    data = await request.get_json()

    inviter = data.get("inviter")
    recipient = data.get("recipient")
    expire_timestamp = data.get("expireTimestamp")

    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        after = await db.execute("INSERT INTO friendRequests (inviter, recipient, expireTimestamp) VALUES (?, ?, ?) RETURNING *", (inviter, recipient, expire_timestamp,))

        after_rows = [dict(row) for row in await after.fetchall()]

        await deliver("friendRequests", after_rows, [])

        await db.commit()

        return jsonify({"message": "Operation successful."}), 200


@friend_request_blueprint.route("/delete", methods=["POST"])
async def delete():
    data = await request.get_json()

    inviter = data.get("inviter")
    recipient = data.get("recipient")

    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("DELETE FROM friendRequests WHERE inviter = ? AND recipient = ? RETURNING *", (inviter, recipient))

        await deliver("partyInvites", [], [dict(row) for row in await cursor.fetchall()])

        await db.commit()
        return jsonify({"message": "Operation successful."}), 200

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= #
__all__ = ["friend_request_blueprint"]