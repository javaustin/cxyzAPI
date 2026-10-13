from quart import request

from app_instance import app

@app.route("/get_manifest", methods = ["GET"])
async def cache():
    data = await request.get_json()

    identifier = request.headers.get("X-Identifier", None)

    # TODO:
    #   Servers are identified by {type}-{number}. Goal: Parse the type, and return the manifest {type}.json
    #   Locate the file named {type}.json
    #   Return it in json format