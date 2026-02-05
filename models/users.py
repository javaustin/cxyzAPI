from quart import request, jsonify, Blueprint
import aiosqlite

import utils
from utils import path, deliver

user_blueprint = Blueprint('user', __name__, url_prefix = "/user")


@user_blueprint.route("/create", methods=["POST"])
async def create():

    data = await request.get_json()  # {'uuid' : 'playerUUID', 'username' : 'cerrot'}
    uuid = data.get("uuid")

    if not uuid:
        return jsonify({"error": "user must have a uuid"}), 400

    columns = ', '.join([x for x in data.keys()])
    placeholders = ', '.join(['?'] * len(data.keys()))
    values = tuple(data.values())

    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row
        try:
            before = await db.execute(f"SELECT * FROM users WHERE uuid = ?", (uuid,))
            original_rows = await before.fetchall()

            if len(original_rows) > 0:
                return jsonify({"error": "duplicate uuids"}), 400

            cursor = await db.execute(f"INSERT INTO users ({columns}) VALUES ({placeholders}) RETURNING *", values)
            new_rows = await cursor.fetchall()

            await db.commit()

        except Exception as ex:
                return jsonify({"error" : ex}), 500

        await deliver("users", [dict(row) for row in new_rows], [])

    return jsonify({"message": "Operation successful.", "uuid": uuid}), 200

@user_blueprint.route("/delete", methods=["POST"])  # similar to get request
async def delete():

    data = await request.get_json()

    uuid = data.get("uuid")

    if not uuid:
        return jsonify({"message", "bruh"}), 404

    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(f"DELETE FROM users WHERE uuid = ? RETURNING *", (uuid,))
        if cursor.rowcount == 0:
            return jsonify({"error": "No user found", "uuid": uuid}), 404

        new_rows = await cursor.fetchall()

        await db.commit()

        await deliver("users", [], [dict(row) for row in new_rows])


    return jsonify({"message": "Operation successful.", "uuid": uuid}), 200

@user_blueprint.route("/modify", methods=["POST"])
async def modify():
    data = await request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400  # bad request
    columns = ", ".join([f"{key} = ?" for key in data.keys()])
    values = list(data.values())
    uuid = data.get("uuid")

    if not uuid:
        return jsonify({"error": "user must have a uuid"}), 400 # Add uuid to the end of the values list for the WHERE clause

    print("user/modify (data): " + str(data))

    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        operation = await db.execute(f"UPDATE users SET {columns} WHERE uuid = '{uuid}' RETURNING *", (*values,))

        new_rows = await operation.fetchall()

        await db.commit()

        if operation.rowcount == 0:
            return jsonify({"error": "UUID not found"}), 404

        await deliver("users", [dict(row) for row in new_rows], [])



    return jsonify({"message": "Operation successful.", "uuid" : uuid}), 200
