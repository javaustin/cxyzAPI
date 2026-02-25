import aiosqlite
from quart import request, jsonify, Blueprint

from other.utils import path, deliver

print(f"loaded {__name__} routes")

party_blueprint = Blueprint('party', __name__, url_prefix = "/party")

# can we rely on the game server to tell us if a player has a party?
# in other words: in what case will the server think that the player owns a party that truly


@party_blueprint.route("/create", methods=["POST"])
async def create():
    data = await request.get_json()

    sender_uuid = data.get("sender_uuid")
    players = data.get("players")
    public = data.get("public")

    if not sender_uuid:
        return jsonify({"error": "uuid is required"}), 400

    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row

        before = await db.execute(f"SELECT * FROM parties WHERE ownerUUID = ?", (sender_uuid,))
        original_rows = await before.fetchall()

        if len(original_rows) > 0:
            return jsonify({"error": "duplicate uuids"}), 400

        after = await db.execute("INSERT INTO parties (ownerUUID, players, public) VALUES (?, ?, ?) RETURNING *", (sender_uuid, players, public,))

        after_rows = [dict(row) for row in await after.fetchall()]

        await deliver("parties", after_rows, [])

        await db.commit()

        return jsonify({"message": "Operation successful."}), 200


@party_blueprint.route("/sync", methods=["POST"])
async def sync():
    data = await request.get_json()

    sender_uuid = data.get("sender_uuid")
    players = data.get("players")
    public = data.get("public")

    if not sender_uuid:
        return jsonify({"error": "uuid is required"}), 400

    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        after = await db.execute("UPDATE parties SET ownerUUID = ?, players = ?, public = ? WHERE ownerUUID RETURNING *", (sender_uuid, players, public,))

        after_rows = [dict(row) for row in await after.fetchall()]

        await deliver("parties", after_rows, [])

        await db.commit()

        return jsonify({"message": "Operation successful."}), 200

@party_blueprint.route("/delete", methods=["POST"])
async def delete():
    data = await request.get_json()

    sender_uuid = data.get("sender_uuid")

    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("DELETE FROM parties WHERE ownerUUID = ? RETURNING *", (sender_uuid,))

        await deliver("parties", [], [dict(row) for row in await cursor.fetchall()])

        await db.commit()

        return jsonify({"message": "Operation successful."}), 200

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= #
__all__ = ["party_blueprint"]