import json

from botocore.exceptions import BotoCoreError, ClientError
from quart import request, jsonify, redirect

from rich import print

from app_instance import app, r2_client, R2_BUCKET


@app.route("/get_artifact", methods=["GET"])
async def get_artifact():

    artifact_path = request.args.get("path")

    if artifact_path is None:
        return jsonify({"error" : "`path` is required"})

    identifier = request.headers.get("X-Identifier")

    if identifier is None:
        # See my comment in manifest.py line 13
        raise RuntimeError("Identifier is required!")

    if "-" not in identifier:
        return {"error": "Could not verify permissions against manifest!"}, 403

    server_type: str = identifier.split("-")[0]

    target_name = server_type.lower()

    json_data : dict = {}
    try:
        with open(f"manifests/{target_name}.json") as f:
            json_data = json.loads(f.read())
    except FileNotFoundError:
        return {"error" : "Could not verify permissions against manifest!"}, 403

    artifacts = json_data["artifacts"]
    artifact_source_paths : list[str] = [artifact["source"] for artifact in artifacts]

    if artifact_path not in artifact_source_paths:
        return jsonify({"error" : "Access denied"}), 403

    print(R2_BUCKET)

    try:
        download_url = r2_client.generate_presigned_url(
            "get_object",
            Params={'Bucket' : R2_BUCKET, 'Key' : artifact_path},
            ExpiresIn=120
        )
    except (BotoCoreError, ClientError):
        print(f"[red]Failed to generate R2 URL for[/red][white]{artifact_path}[/white]")

        return jsonify({"error": "Artifact download is temporarily unavailable"}), 503

    return redirect(download_url, 302)

