import aiosqlite
from quart import request, jsonify, Blueprint

from utils import path, deliver, ship

punishment_blueprint = Blueprint('punishment', __name__, url_prefix = "/punishment")

#
# async def validate_user(obj : dict):
#     # Adds the players uuid to the record if not already present
#
#     username = obj.get("username")
#
#     res = await get_user_by_username(username)
#
#     if res[1] < 200 or res[1] >= 300: # error code
#         return {"message" : "system.errors.player-not-found"}
#
#     obj["uuid"] = res[0].get("uuid")
#
#     return obj

@punishment_blueprint.route("/set", methods=["POST"])
async def set():
    # Accepts a punishment object. Returns an ID for it to use.

    data = await request.get_json()


    punishment : dict = data.get("punishment")
    # punishment = await validate_user(punishment)

    if "message" in punishment.keys():
        return {"message" : punishment.get("message")}, 400

    keys = []
    values = []

    for key in punishment.keys():
        key = key
        value = punishment.get(key)

        keys.append(key)
        values.append(value)

    possible_id = punishment["id"]


    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        try:
            query = f"INSERT INTO punishments ({', '.join(keys)}) VALUES ({('?, ' * len(values))[:-2]})"
            print(query, values)
            cursor = await db.execute(query, values,)

            punishment["id"] = cursor.lastrowid

            if punishment["id"] != possible_id:
                # The game server provided us with an invalid ID, we must resend all the punishments to the game servers to ensure consistency.
                await ship(table = "punishments")

            await db.commit()

        except aiosqlite.OperationalError as ex:
            return jsonify({"error" : str(ex)}), 500

        return jsonify({"message" : "Operation successful!", "punishment" : punishment}), 200


@punishment_blueprint.route("/delete", methods = ["POST"])
async def delete():
    data = await request.get_json()

    id = data.get("id")

    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        punishment = {}

        try:
            cursor = await db.execute(f"DELETE FROM punishments WHERE id = {id} RETURNING *")
            deleted_rows = await cursor.fetchall()

            await deliver("punishments", [], [dict(row) for row in deleted_rows])
            # The plugin will remove the old rows (or single row in this case, and not add any new ones, since that argument is left blank)

            await db.commit()

        except aiosqlite.OperationalError as ex:
            return jsonify({"error" : str(ex)}), 500

        return jsonify({"message" : "Operation successful!", "punishment" : punishment}), 200


@punishment_blueprint.route("/edit", methods=["POST"])
async def edit():
    # Accepts a punishment object, an ID must be included in the object.

    data = await request.get_json()

    punishment : dict = data.get("punishment")
    id = punishment.get("id")

    if not id:
        return jsonify({"message": "id cannot be null"}), 400

    if punishment is None:
        return {"message": "system.errors.args.missing-case"}, 404

    columns = ', '.join([f"{key} = ?" for key in punishment])
    values = list(punishment.values())

    query = f"UPDATE punishments SET {columns} WHERE id = {id}"

    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        try:
            before = await db.execute(f"SELECT * FROM punishments WHERE id = {id}")
            original_rows = await before.fetchall()

            operation = await db.execute(query, values)

            new_rows = await operation.fetchall()

            if operation.rowcount == 0:
                return {"message" : "system.errors.args.missing-case"}, 404

            await deliver("punishments", [dict(row) for row in new_rows], [dict(row) for row in original_rows])

            await db.commit()

        except aiosqlite.OperationalError as ex:
            return jsonify({"error" : str(ex)}), 500

        return jsonify({"message" : "Operation successful!", "punishment" : punishment}), 200


__all__ = ["punishment_blueprint"]