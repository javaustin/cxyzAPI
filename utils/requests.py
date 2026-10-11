import json
import time
from urllib.parse import urlparse

import httpx
from utils.auth import generate_signature
from utils.registry import ServerRegistry
from utils.servers import Server

from rich import print

async def post_request(url : str, data : dict):
    try:
        async with httpx.AsyncClient() as client:
            identifier : str = ServerRegistry.api.identifier
            secret : str = ServerRegistry.api.secret
            timestamp : int = int(time.time())

            urlpath : str = urlparse(url).path

            payload = json.dumps(data, separators=(',', ':'))

            signature = generate_signature(identifier = identifier, secret = secret, timestamp = timestamp, method = "POST", urlpath = urlpath, payload_json = payload)

            print(f"[cyan]POST in progress:[/cyan] [white]{url}[/white]")
            result = await client.post(url, json = data, headers =
                    {
                    'Content-Type' : "application/json",
                    'X-Identifier' : ServerRegistry.api.identifier,
                    'X-Timestamp' : str(timestamp),
                    'X-Signature' : signature
                    },
                              timeout = 5.0
                              )


            if result.status_code < 200 or result.status_code >= 300:
                print(f"[white]POST COMPLETED[/white] [yellow]({result.status_code})[/yellow] [white]{url}.[/white]\n\t[white]Response: {json.dumps(result.json(), separators=(',', ':'))}[/white]")

            if 200 <= result.status_code < 300:
                print(f"[white]POST COMPLETED[/white] [green]({result.status_code})[/green] [white]{url}.[/white]\n\t[white]Response: {json.dumps(result.json(), separators=(',', ':'))}[/white]")

            return result.json(), result.status_code

    except Exception as ex:
        print(f"[red]POST FAILED[/red] {url}.\n\t{ex}")
        return None, None
