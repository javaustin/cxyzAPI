from quart import request

from app_instance import app


@app.route("/get_artifact", methods = ["GET"])
async def cache():
    data = await request.get_json()

    identifier = request.headers.get("X-Identifier", None)

    # TODO
    #   Servers are identified by {type}-{number}. Goal: Parse the type, and read the manifest {type}.json
    #   Compare the requested file path with the manifest. If it is not contained in the manifest then the client does not get it.
    #   Connect to R2 object storage and return the file