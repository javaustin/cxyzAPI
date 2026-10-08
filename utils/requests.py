import json
import time
from urllib.parse import urlparse

import httpx
from utils.auth import generate_signature
from utils.servers import Server

from rich import print

async def post_request(url : str, data : dict):
    try:
        async with httpx.AsyncClient() as client:
            identifier : str = Server.api.identifier
            secret : str = Server.api.secret
            timestamp : int = int(time.time())

            urlpath : str = urlparse(url).path

            payload = json.dumps(data, separators=(',', ':'))

            signature = generate_signature(identifier = identifier, secret = secret, timestamp = timestamp, method = "POST", urlpath = urlpath, payload_json = payload)

            print(f"[cyan]POST in progress:[/cyan] {url}")
            result = await client.post(url, json = data, headers =
                    {
                    'Content-Type' : "application/json",
                    'X-Identifier' : Server.api.identifier,
                    'X-Timestamp' : str(timestamp),
                    'X-Signature' : signature
                    },
                              timeout = 5.0
                              )


            if result.status_code != 200:
                print(f"[yellow]POST COMPLETED ({result.status_code}) {url}.\n\tResponse: {json.dumps(result.json(), separators=(',', ':'))}[/yellow]")

            if result.status_code == 200:
                print(f"[green]POST COMPLETED ({result.status_code}) {url}.\n\tResponse: {json.dumps(result.json(), separators=(',', ':'))}[/green]")


            return None

    except Exception as ex:
        print(f"[red]POST FAILED[/red] {url}.\n\t{ex}")
        return None
