import json

def get(key : str):
    with open("config.json", "r") as f:
        data = json.load(f)

        return data.get(key)

api_key = get("api-key")
path = get("db-path")
quart_port = get("quart-port")
quart_host = get("quart-host")
enabled_logs : list = get("enabled-logs")
timezone : str = get("timezone")
do_extended_logs : bool = get("do-extended-logs")