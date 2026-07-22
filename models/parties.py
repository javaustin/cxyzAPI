import aiosqlite
from quart import request, jsonify, Blueprint

import app_instance
from other.utils import path, deliver

print(f"loaded {__name__} routes")

party_blueprint = Blueprint('party', __name__, url_prefix = "/party")

@party_blueprint.route("/create", methods=["POST"])
async def create():
    data = await request.get_json()

    sender_uuid = data.get("sender_uuid")
    players = data.get("players")
    public = data.get("public")

    if not sender_uuid:
        return jsonify({"error" : "uuid is required"}), 400

    db = app_instance.db

    try:
        after = await db.execute("INSERT INTO parties (ownerUUID, players, public) VALUES (?, ?, ?) RETURNING *", (sender_uuid, players, public,))

        after_rows = [dict(row) for row in await after.fetchall()]

        await deliver("parties", after_rows, [])

        await after.close()
        await db.commit()


        return jsonify({"message": "Operation successful."}), 200

    except aiosqlite.IntegrityError:
        # Unique constraint failed
        return jsonify({"error" : "duplicate uuid"}), 400

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 500



@party_blueprint.route("/sync", methods=["POST"])
async def sync():
    data = await request.get_json()

    sender_uuid = data.get("sender_uuid")
    players = data.get("players")
    public = data.get("public")

    if not sender_uuid:
        return jsonify({"error" : "uuid is required"}), 400

    db = app_instance.db

    try:
        after = await db.execute("UPDATE parties SET ownerUUID = ?, players = ?, public = ? WHERE ownerUUID RETURNING *", (sender_uuid, players, public,))

        after_rows = [dict(row) for row in await after.fetchall()]

        await deliver("parties", after_rows, [])

        await after.close()
        await db.commit()


        return jsonify({"message": "Operation successful."}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 500


@party_blueprint.route("/delete", methods=["POST"])
async def delete():
    data = await request.get_json()

    sender_uuid = data.get("sender_uuid")

    db = app_instance.db

    try:
        cursor = await db.execute("DELETE FROM parties WHERE ownerUUID = ? RETURNING *", (sender_uuid,))

        await deliver("parties", [], [dict(row) for row in await cursor.fetchall()])

        await cursor.close()
        await db.commit()


        return jsonify({"message": "Operation successful."}), 200


    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 500


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= #
__all__ = ["party_blueprint"]