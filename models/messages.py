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
        return jsonify({"error": "Missing required parameters"}), 400

    columns = ", ".join(data.keys())
    values = list(data.values())

    db = app_instance.db

    try:
        await db.execute("PRAGMA journal_mode=WAL;")
        db.row_factory = aiosqlite.Row

        before = await db.execute(f"SELECT * FROM messages WHERE recipient_uuid = '{recipient_uuid}' AND sender_uuid = '{sender_uuid}' AND timestamp = {timestamp} AND content = '{content}'")
        old_rows = await before.fetchall()

        after = await db.execute(f"INSERT INTO messages ({columns}) VALUES (?, ?, ?, ?, ?, ?)", values)

        new_rows = await after.fetchall()

        await deliver("messages", [dict(row) for row in new_rows], [dict(row) for row in old_rows])

        await db.commit()

        return jsonify({"message": "Operation successful.", "message_data": data}), 200
    # sender_uuid, sender_name, recipient_uuid, recipient_name, content, timestamp

    except aiosqlite.OperationalError as ex:
        return jsonify({"error", str(ex)}), 500


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= #
__all__ = ["message_blueprint"]