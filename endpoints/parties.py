import aiosqlite
from quart import request, jsonify, Blueprint

import app_instance

from utils.deliveries import deliver


party_blueprint = Blueprint('party', __name__, url_prefix = "/party")

@party_blueprint.route("/create", methods=["POST"])
async def create():
    data = await request.get_json()

    sender_uuid = data.get("sender_uuid")
    players = data.get("players")
    public = data.get("public")

    if not sender_uuid:
        return jsonify({"error": "`sender_uuid` is a required argument"}), 400

    db = app_instance.db

    try:
        async with app_instance.db_lock:
            after = await db.execute("INSERT INTO parties (ownerUUID, players, public) VALUES (?, ?, ?) RETURNING *", (sender_uuid, players, public,))
            after_rows = [dict(row) for row in await after.fetchall()]
            await after.close()
            await db.commit()

        await deliver("parties", after_rows, [])


        return jsonify({"message": "Operation successful"}), 200

    except aiosqlite.IntegrityError:
        # Unique constraint failed
        return jsonify({"error": "`sender_uuid` already exists"}), 400

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 400



@party_blueprint.route("/sync", methods=["POST"])
async def sync():
    data = await request.get_json()

    sender_uuid = data.get("sender_uuid")
    players = data.get("players")
    public = data.get("public")

    if not sender_uuid:
        return jsonify({"error": "`sender_uuid` is a required argument"}), 400

    db = app_instance.db

    try:
        async with app_instance.db_lock:
            after = await db.execute("UPDATE parties SET ownerUUID = ?, players = ?, public = ? WHERE ownerUUID RETURNING *", (sender_uuid, players, public,))
            after_rows = [dict(row) for row in await after.fetchall()]
            await after.close()
            await db.commit()

        await deliver("parties", after_rows, [])


        return jsonify({"message": "Operation successful"}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 400


@party_blueprint.route("/delete", methods=["POST"])
async def delete():
    data = await request.get_json()

    sender_uuid = data.get("sender_uuid")

    db = app_instance.db

    try:
        async with app_instance.db_lock:
            cursor = await db.execute("DELETE FROM parties WHERE ownerUUID = ? RETURNING *", (sender_uuid,))
            deleted_rows = [dict(row) for row in await cursor.fetchall()]
            await cursor.close()
            await db.commit()

        await deliver("parties", [], deleted_rows)


        return jsonify({"message": "Operation successful"}), 200


    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 400


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= #
__all__ = ["party_blueprint"]
