import json

import aiosqlite
import quart

import app_instance
from utils.auth import authenticate_request
from utils.errors import MissingHeadersException, DuplicateRequestException


async def check_is_unique(request : quart.app.Request):

    data = await request.get_data(as_text = True)

    request_id = request.headers.get("X-Request-ID", None)
    request_body : str = data
    identifier = request.headers.get("X-Identifier", None)
    timestamp_string  = request.headers.get("X-Timestamp")
    urlpath : str = request.path
    method : str = request.method

    if identifier is None:
        raise MissingHeadersException("\"X-Identifier\" is required for interacting with this service.")

    if timestamp_string is None:
        raise MissingHeadersException("\"X-Timestamp\" is required for interacting with this service.")

    if request_id is None:
        raise MissingHeadersException("\"X-Request-ID\" is required for interacting with this service.")

    timestamp = int(timestamp_string)

    try:
        db = app_instance.db
        async with app_instance.db_lock:
            cursor = await db.execute(
                """INSERT INTO requests 
                   (request_id, path, method, timestamp, server_id, ip_address, request_body, status_code, response_body) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (request_id, urlpath, method, timestamp, identifier, request.remote_addr, json.dumps(request_body), 0, "",)
            )

            await cursor.close()
            await db.commit()

    except aiosqlite.IntegrityError:
        raise DuplicateRequestException(f"Request with ID={request_id} already exists.")

async def preprocess_request(request : quart.app.Request):
    await authenticate_request(request)
    await check_is_unique(request)

    return None

async def log_after_request(original_request : quart.app.Request, response : quart.app.Response):

    status_code : int = response.status_code
    response_body = await response.get_data(as_text = True)

    request_id = original_request.headers.get("X-Request-ID")

    db = app_instance.db
    async with app_instance.db_lock:
        cursor = await db.execute(
            """UPDATE requests SET status_code = ?, response_body = ? WHERE request_id = ?""",
                                  (status_code, response_body, request_id,)
        )

        await cursor.close()
        await db.commit()

