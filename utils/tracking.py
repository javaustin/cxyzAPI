import datetime
import inspect
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import aiosqlite
import quart

from rich import print

import app_instance
from utils.auth import authenticate_request
from utils.config import timezone, enabled_logs, do_extended_logs
from utils.errors import MissingHeadersException, DuplicateRequestException


async def check_is_unique(request : quart.app.Request):

    data = await request.get_data(as_text = True)

    request_id = request.headers.get("X-Request-ID", None)
    request_body : str = data
    identifier = request.headers.get("X-Identifier", None)
    declared_timestamp_string  = request.headers.get("X-Timestamp")
    urlpath : str = request.path
    method : str = request.method

    # Keep enough request metadata to record the failure even when the
    # timestamp supplied by the client is malformed.  Validation happens
    # below, after the request has been persisted.
    try:
        declared_timestamp = int(declared_timestamp_string) if declared_timestamp_string is not None else int(time.time())
    except (TypeError, ValueError):
        declared_timestamp = int(time.time())

    try:
        db = app_instance.db
        async with app_instance.db_lock:
            cursor = await db.execute(
                """INSERT INTO requests 
                   (request_id, path, method, declared_timestamp, real_timestamp, server_id, ip_address, request_body, status_code, response_body) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (request_id, urlpath, method, declared_timestamp, int(time.time()), identifier, request.remote_addr, request_body, 0, "",)
            )

            await cursor.close()
            await db.commit()

            if identifier is None:
                raise MissingHeadersException("\"X-Identifier\" is required for interacting with this service.")

            if declared_timestamp_string is None:
                raise MissingHeadersException("\"X-Timestamp\" is required for interacting with this service.")

            if request_id is None:
                raise MissingHeadersException("\"X-Request-ID\" is required for interacting with this service.")

    except aiosqlite.IntegrityError:
        raise DuplicateRequestException(f"Request with ID={request_id} has already been processed.")

async def preprocess_request(request : quart.app.Request):
    await check_is_unique(request)
    await authenticate_request(request)

    return None

async def log_after_request(original_request : quart.app.Request, response : quart.app.Response):

    status_code : int = response.status_code

    request_id = original_request.headers.get("X-Request-ID")
    identifier = original_request.headers.get("X-Identifier")

    og_data = await original_request.get_data(as_text = True)
    request_body : str = og_data

    result = response.get_data(as_text=True)
    response_body = await result if inspect.isawaitable(result) else result

    db = app_instance.db
    async with app_instance.db_lock:
        cursor = await db.execute(
            """UPDATE requests SET status_code = ?, response_body = ? WHERE request_id = ?""",
            (status_code, response_body, request_id,)
        )

        # Normally check_is_unique() creates the row before the request is
        # handled.  If validation failed before that insert (or the request
        # entered the app through another path), do not silently lose the
        # completed response.  Persist it here instead.
        if cursor.rowcount == 0:
            await cursor.close()
            await db.execute(
                """INSERT INTO requests
                   (request_id, path, method, declared_timestamp, real_timestamp, server_id, ip_address, request_body, status_code, response_body)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    request_id,
                    original_request.path,
                    original_request.method,
                    int(time.time()),
                    int(time.time()),
                    identifier,
                    original_request.remote_addr,
                    request_body,
                    status_code,
                    response_body,
                )
            )
        else:
            await cursor.close()
        await db.commit()

    is_success = 200 <= status_code < 300

    ftime = datetime.now(ZoneInfo(timezone)).strftime("%b-%d-%Y %H:%M:%S %Z")
    status_color = "[green]" if is_success else "[red]"

    if is_success and not enabled_logs.__contains__("REQUEST_SUCCESS"):
        return

    if not is_success and not enabled_logs.__contains__("REQUEST_FAIL"):
        return

    print(f"[magenta][{ftime}][/magenta] [yellow]{original_request.method}[/yellow] [white]{original_request.path}[/white] [white]request_id={request_id} identifier={identifier} {original_request.remote_addr}[/white] {status_color}{status_code}{status_color.replace('[', '[/')}")

    if not do_extended_logs:
        return

    if len(request_body) > 0:
        print(f"\t[white]Body: {request_body}[/white]")
    print(f"\t[white]Response[/white] {status_color}({status_code}):{status_color.replace('[', '[/')} [white]{response_body}[/white]")
