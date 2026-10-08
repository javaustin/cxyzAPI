import base64
import hashlib
import hmac
import time

import quart

from utils.errors import MissingHeadersException, AuthenticationFailException
from utils.servers import Server

def generate_signature(identifier : str, secret : str, timestamp : int, method : str, urlpath : str, payload_json : str):
    if payload_json is None:
        payload_json = ""

    message = identifier + " | " + str(timestamp) + " | " + method + " | " + urlpath + " | " + payload_json

    mac = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256)

    signature = base64.b64encode(mac.digest()).decode('utf-8')

    return signature

async def authenticate_request(request : quart.app.Request):

    data = await request.get_data(as_text = True)

    payload : str = data
    identifier = request.headers.get("X-Identifier", None)
    timestamp_string  = request.headers.get("X-Timestamp", None)
    signature  = request.headers.get("X-Signature", None)
    urlpath : str = request.path
    method : str = request.method

    print(f"Authenticating {method} '{urlpath}' from '{identifier}' with {f"payload:\n{payload}" if len(payload) > 0 else "no body."}")

    if identifier is None:
        raise MissingHeadersException("\"X-Identifier\" is required for interacting with this service.")

    if timestamp_string is None:
        raise MissingHeadersException("\"X-Timestamp\" is required for interacting with this service.")

    if signature is None:
        raise MissingHeadersException("\"X-Signature\" is required for interacting with this service.")

    try:
        provided_timestamp : int = int(timestamp_string)

    except Exception:
        raise AuthenticationFailException("Timestamp is invalid.")

    if (abs(time.time()) - abs(provided_timestamp)) > 30:
        raise AuthenticationFailException("Request timestamp expired.")

    server = Server.get_server(identifier)

    if server is None:
        raise AuthenticationFailException(f"No service with identifier '{identifier}' is registered in the API config.")

    local_signature = generate_signature(
        identifier = server.identifier,
        secret = server.secret,
        timestamp = provided_timestamp,
        method = method,
        urlpath = urlpath,
        payload_json = payload
    )

    if not hmac.compare_digest(signature, local_signature):
        raise AuthenticationFailException("Signature is invalid.")