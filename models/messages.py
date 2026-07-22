from quart import request, jsonify, Blueprint
import aiosqlite

import app_instance
from other.utils import deliver

print(f"loaded {__name__} routes")

message_blueprint = Blueprint('message', __name__, url_prefix = "/message")


@message_blueprint.route("/submit", methods = ["POST"])
async def submit():

    data = await request.get_json()

    sender_uuid = data.get("sender_uuid")
    sender_name = data.get("sender_name")
    recipient_uuid = data.get("recipient_uuid")
    recipient_name = data.get("recipient_name")
    content = data.get("content")
    timestamp = data.get("timestamp")

    if not all([sender_uuid, sender_name, recipient_uuid, recipient_name, timestamp]): # We exclude 'content' because we allow that to be null
        return jsonify({"error" : "Missing required parameters"}), 400

    columns = ", ".join(data.keys())
    values = list(data.values())

    db = app_instance.db

    try:
        before = await db.execute(f"SELECT * FROM messages WHERE recipient_uuid = '{recipient_uuid}' AND sender_uuid = '{sender_uuid}' AND timestamp = {timestamp} AND content = '{content}'")
        old_rows = await before.fetchall()

        after = await db.execute(f"INSERT INTO messages ({columns}) VALUES (?, ?, ?, ?, ?, ?)", values)

        new_rows = await after.fetchall()

        await deliver("messages", [dict(row) for row in new_rows], [dict(row) for row in old_rows])

        await before.close()
        await after.close()

        await db.commit()


        return jsonify({"message": "Operation successful.", "message_data": data}), 200
    # sender_uuid, sender_name, recipient_uuid, recipient_name, content, timestamp

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 500

@message_blueprint.route("/query", methods=["POST"])  # similar to get request
async def query():

    data = await request.get_json()

    sender_uuid = data.get("sender_uuid")
    recipient_uuid = data.get("recipient_uuid")
    content = data.get("content")
    timestamp = data.get("after_timestamp")

    db = app_instance.db

    try:
        filters : list[str] = []
        params : list[str] = []

        if sender_uuid:
            filters.append(f"sender_uuid = ?")
            params.append(sender_uuid)

        if recipient_uuid:
            filters.append(f"recipient_uuid = ?")
            params.append(recipient_uuid)

        if content:
            filters.append(f"content = ?")
            params.append(content)

        if timestamp:
            filters.append(f"timestamp >= ?")
            params.append(timestamp)

        if len(filters) == 0:
            cursor = await db.execute("SELECT * FROM messages")
        else:
            cursor = await db.execute(f"SELECT * FROM messages WHERE {'AND '.join(filters)}", params)

        rows = await cursor.fetchall()

        if len(rows) == 0:
            return jsonify({"error" : "No messages found"}), 404

        await cursor.close()

        return jsonify({"messages": [dict(row) for row in rows]}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 500

@message_blueprint.route("/delete", methods=["POST"])  # similar to get request
async def delete():

    data = await request.get_json()

    sender_uuid = data.get("sender_uuid")
    recipient_uuid = data.get("recipient_uuid")
    content = data.get("content")
    timestamp = data.get("timestamp")

    db = app_instance.db

    try:
        filters : list[str] = []
        params : list[str] = []

        if sender_uuid:
            filters.append(f"sender_uuid = ?")
            params.append(sender_uuid)

        if recipient_uuid:
            filters.append(f"recipient_uuid = ?")
            params.append(recipient_uuid)

        if content:
            filters.append(f"content = ?")
            params.append(content)

        if timestamp:
            filters.append(f"timestamp > ?")
            params.append(timestamp)

        if len(filters) == 0:
            return jsonify({"error" : "Please specify any of the following arguments: sender_uuid, recipient_uuid, content, timestamp"}), 400

        cursor = await db.execute(f"DELETE FROM messages WHERE {'AND '.join(filters)} RETURNING *", params)

        new_rows = await cursor.fetchall()

        await cursor.close()
        await db.commit()

        await deliver("messages", [], [dict(row) for row in new_rows])

        return jsonify({"message": f"Operation successful. {len(new_rows)} rows affected."}), 200

    except aiosqlite.OperationalError as ex:
        return jsonify({"error" : str(ex)}), 500


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= #
__all__ = ["message_blueprint"]