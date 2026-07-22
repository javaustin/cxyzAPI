from quart import request, jsonify, Blueprint
import aiosqlite

import app_instance
from other.utils import deliver

print(f"loaded {__name__} routes")

user_blueprint = Blueprint('user', __name__, url_prefix = "/user")

@user_blueprint.route("/get_user/<uuid>", methods=["GET"])
async def get_user(uuid):

    if not uuid:
        return jsonify({"error" : "UUID required"}), 400  # bad request

    db = app_instance.db

    try:
        cursor = await db.execute(f"SELECT * FROM users WHERE uuid = ?", (uuid,))
        rows = await cursor.fetchall()

        await cursor.close()

        if len(rows) >= 2:
            print(f"[!] At least two rows both contain the same uuid={uuid}!")

        if len(rows) == 0:
            return jsonify({"message" : "User not found!"}), 404

        return jsonify(dict(rows[0])), 200


    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 500

@user_blueprint.route("/get_user_attribute/<uuid>/<attribute>", methods=["GET"])
async def get_user_attribute(uuid, attribute):

    db = app_instance.db

    try:

        cursor = await db.execute(f"SELECT * FROM users WHERE uuid = ?", (uuid,))
        rows = await cursor.fetchall()

        await cursor.close()

        if len(rows) >= 2:
            print(f"[!] At least two rows both contain the same uuid={uuid}!")

        if len(rows) == 0:
            return jsonify({"message" : "User not found!"}), 404

        row : dict = dict(rows[0])

        try:
            return jsonify({attribute : row[attribute]}), 200

        except KeyError:
            return jsonify({"message" : f"Attribute {attribute} does not exist."}), 400

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 500


@user_blueprint.route("/create", methods=["POST"])
async def create():

    data = await request.get_json()  # {'uuid' : 'playerUUID', 'username' : 'cerrot'}
    uuid = data.get("uuid")

    if not uuid:
        return jsonify({"error" : "UUID required"}), 400

    columns = ', '.join([x for x in data.keys()])
    placeholders = ', '.join(['?'] * len(data.keys()))
    values = tuple(data.values())

    db = app_instance.db

    try:
        cursor = await db.execute(f"INSERT INTO users ({columns}) VALUES ({placeholders}) RETURNING *", values)
        new_rows = await cursor.fetchall()

        await cursor.close()
        await db.commit()

        await deliver("users", [dict(row) for row in new_rows], [])

        return jsonify({"message": "Operation successful.", "uuid": uuid}), 200

    except aiosqlite.IntegrityError:
        # Unique constraint failed
        return jsonify({"error" : "duplicate uuid"}), 400

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 500



@user_blueprint.route("/delete", methods=["POST"])  # similar to get request
async def delete():

    data = await request.get_json()

    uuid = data.get("uuid")

    if not uuid:
        return jsonify({"message", "UUID required"}), 404

    db = app_instance.db

    try:

        cursor = await db.execute(f"DELETE FROM users WHERE uuid = ? RETURNING *", (uuid,))

        new_rows = await cursor.fetchall()

        if len(new_rows) == 0:
            return jsonify({"error" : "No user found", "uuid": uuid}), 404

        await cursor.close()
        await db.commit()


        await deliver("users", [], [dict(row) for row in new_rows])

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 500


    return jsonify({"message": "Operation successful.", "uuid": uuid}), 200

@user_blueprint.route("/modify", methods=["POST"])
async def modify():
    data = await request.get_json()

    if not data:
        return jsonify({"error" : "No data provided"}), 400  # bad request

    columns = ", ".join([f"{key} = ?" for key in data.keys()])
    values = list(data.values())
    uuid = data.get("uuid")
    version = data.get("version")

    try:
        version = int(version)
    except ValueError:
        return jsonify({"error" : "version must be an integer"}), 400

    if not uuid:
        return jsonify({"error" : "user must have a uuid"}), 400

    if version is None:
        return jsonify({"error" : "user must have a version"}), 400

    db = app_instance.db

    try:
        cursor = await db.execute(f"UPDATE users SET {columns} WHERE uuid = '{uuid}' AND version < {version} RETURNING *", (*values,))

        new_rows = await cursor.fetchall()

        await cursor.close()
        await db.commit()


        if len(new_rows) == 0:
            return jsonify({"error" : "No rows affected on SQL operation. Either the uuid is invalid or the object version is not synced."}), 404

        await deliver("users", [dict(row) for row in new_rows], [])

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 500

    return jsonify({"message": "Operation successful.", "uuid" : uuid}), 200
