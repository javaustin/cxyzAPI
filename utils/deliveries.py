import app_instance
from utils.registry import ServerRegistry
from utils.servers import Server
from utils.requests import post_request

class DeliveryService:
    is_delivering = False
    tables_to_deliver = [
        "parties",
        "messages",
        "users",
        "punishments",
        "partyInvites",
        "friendRequests",
        "gameStats"
    ]


async def ship(table : str = "users"):
    # Sends a json copy of an entire table to all game servers.

    db = app_instance.db

    try:
        async with app_instance.db_lock:
            cursor = await db.execute(f"SELECT * FROM {table}")
            res = await cursor.fetchall()
            await cursor.close()

        for server in ServerRegistry.servers:
            await post_request(f"{server.ip}/{table}Shipment", {"data" : [dict(row) for row in res]})

    except Exception as ex:
        raise RuntimeError(ex)

async def deliver(table : str, new_rows : list, old_rows : list):
    # Sends a json copy of any updated rows to all game servers.

    new_data = [dict(row) for row in new_rows]
    old_data = [dict(row) for row in old_rows]

    if len(new_data) == 0 and len(old_data) == 0:
        return None

    for server in ServerRegistry.servers:
        await post_request(
            f"{server.ip}/{table}Delivery",
            {
                "new_data": new_data,
                "old_data": old_data
            }
        )

    return None
