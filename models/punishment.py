import aiosqlite
from quart import request, jsonify, Blueprint

import app_instance
from other.utils import path, deliver, ship

print(f"loaded {__name__} routes")

punishment_blueprint = Blueprint('punishment', __name__, url_prefix = "/punishment")

async def get_sequence_id() -> int:
    db = app_instance.db

    await db.execute("PRAGMA journal_mode=WAL;")
    db.row_factory = aiosqlite.Row

    cursor = await db.execute(f"SELECT * FROM sqlite_sequence WHERE name = 'punishments'")

    res = await cursor.fetchone()

    if res is not None:
        return int(res["seq"])

    return 0


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

    keys = []
    values = []

    for key in punishment.keys():
        key = key
        value = punishment.get(key)

        keys.append(key)
        values.append(value)


    db = app_instance.db

    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        query = f"INSERT INTO punishments ({', '.join(keys)}) VALUES ({('?, ' * len(values))[:-2]}) RETURNING *"
        cursor = await db.execute(query, values,)

        new_rows = await cursor.fetchall()

        await db.commit()

        if reship:
            await ship("punishments")

        else:
            await deliver("punishments", new_rows, [])

        return jsonify({"message": "Operation successful!", "punishment": punishment}), 200


    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 500


@punishment_blueprint.route("/delete", methods = ["POST"])
async def delete():
    data = await request.get_json()

    id = data.get("id")

    db = app_instance.db

    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        punishment = {}

        cursor = await db.execute(f"DELETE FROM punishments WHERE id = {id} RETURNING *")
        deleted_rows = await cursor.fetchall()


        await deliver("punishments", [], [dict(row) for row in deleted_rows])
        # The plugin will remove the old rows (or single row in this case, and not add any new ones, since that argument is left blank)

        await db.commit()

        return jsonify({"message": "Operation successful!", "punishment": punishment}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 500


@punishment_blueprint.route("/edit", methods=["POST"])
async def edit():
    # Accepts a punishment object, an ID must be included in the object.

    data = await request.get_json()

    punishment : dict = data.get("punishment")
    case_id = punishment.get("id")

    if not case_id:
        return jsonify({"message": "id cannot be null"}), 400

    if punishment is None:
        return {"message": f"punishment with id={case_id} can't be found"}, 404

    columns = ', '.join([f"{key} = ?" for key in punishment])
    values = list(punishment.values())

    query = f"UPDATE punishments SET {columns} WHERE id = {case_id}"

    db = app_instance.db

    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        operation = await db.execute(query, values)

        new_rows = await operation.fetchall()

        if len(new_rows) == 0:
            return jsonify({"message": "No row found"}), 404

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

    db = app_instance.db

    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        operation = await db.execute("DELETE FROM punishments WHERE uuid = ? RETURNING *", (uuid,))

        deleted_rows = await operation.fetchall()

        await deliver("punishments", [], [dict(row) for row in deleted_rows])

        await db.commit()
        return jsonify({"message" : "Operation successful!"}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 500



__all__ = ["punishment_blueprint"]