import json

from quart import jsonify, request

from app_instance import app

@app.route("/get_manifest", methods = ["GET"])
async def get_manifest():

    identifier = request.headers.get("X-Identifier")

    if identifier is None:
        # I put the check here to appease the linter
        # Identifier should always be pre-verified by the auth system - which happens before this function is called.
        # If this condition is ever true this would be a huge problem because that means authentication failed to even run.
        raise RuntimeError("Identifier is required!")

    if "-" not in identifier:
        return {"error" : "Manifest not found!"}

    server_type : str = identifier.split("-")[0]

    target_name = server_type.lower()

    json_data : dict = {}
    try:
        with open(f"manifests/{target_name}.json") as f:
            json_data = json.loads(f.read())
    except FileNotFoundError:
        return {"error" : "Manifest not found!"}, 404

    return jsonify(json.dumps(json_data)), 200