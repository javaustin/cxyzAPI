import aiosqlite
from quart import request, jsonify, Blueprint

from other.utils import path, deliver, ship

print(f"loaded {__name__} routes")

punishment_blueprint = Blueprint('punishment', __name__, url_prefix = "/punishment")

async def get_sequence_id() -> int:
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(f"SELECT * FROM sqlite_sequence WHERE name = 'punishments'")

        res = await cursor.fetchone()

        return int(res["seq"])


@punishment_blueprint.route("/set", methods=["POST"])
async def set():
    # Accepts a punishment object. Returns an ID for it to use.

    data = await request.get_json()


    punishment : dict = data.get("punishment")

    if "message" in punishment.keys():
        return {"message" : punishment.get("message")}, 400

    last_id = await get_sequence_id()
    

    reship = False
    if punishment["id"] <= last_id:
        punishment["id"] = last_id + 1
        reship = True

    print("punishment: " + str(punishment))
    print("last_id: " + str(last_id))

    keys = []
    values = []

    for key in punishment.keys():
        key = key
        value = punishment.get(key)

        keys.append(key)
        values.append(value)


    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        try:
            query = f"INSERT INTO punishments ({', '.join(keys)}) VALUES ({('?, ' * len(values))[:-2]}) RETURNING *"
            cursor = await db.execute(query, values,)

            new_rows = await cursor.fetchall()

            await db.commit()

            if reship:
                await ship("punishments")

            else:
                await deliver("punishments", new_rows, [])

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

            await deliver("punishments", [dict(row) for row in new_rows], [])

            await db.commit()

        except aiosqlite.OperationalError as ex:
            return jsonify({"error" : str(ex)}), 500

        return jsonify({"message" : "Operation successful!", "punishment" : punishment}), 200

@punishment_blueprint.route("/clear", methods=["POST"])
async def clear():

    data = await request.get_json()
    uuid : str = data.get("uuid")

    if not uuid:
        return jsonify({"message": "uuid cannot be null"}), 400

    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        try:
            operation = await db.execute("DELETE FROM punishments WHERE uuid = ? RETURNING *", (uuid,))

            deleted_rows = await operation.fetchall()

            await deliver("punishments", [], [dict(row) for row in deleted_rows])

            await db.commit()

        except aiosqlite.OperationalError as ex:
            return jsonify({"error" : str(ex)}), 500

        return jsonify({"message" : "Operation successful!"}), 200


__all__ = ["punishment_blueprint"]