import os
import re
from typing import Optional

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from werkzeug.exceptions import abort

from grafener.logging_config import init_logging
from grafener.request_handler import get_metrics, get_data

init_logging()

app = Flask(__name__)
cors = CORS(app)


def _check_source():
    """
    checks HTTP header source is present and points to an available resource

    :return: parse HTTP header source
    """
    source: str = request.headers.get("source")

    if not source:
        abort(Response("HTTP header 'source' not found", 400))
    if re.match("ĥttp[s]?://", source):
        abort(Response("HTTP source not supported", 400))
    if source.startswith("s3://"):
        abort(Response("S3 source not supported", 400))

    if not os.path.exists(source):
        abort(Response("couldn't find source [{}]".format(source), 400))

    return source


@app.route("/", methods=["GET"])
@app.route("/<xp>", methods=["GET"])
def health_check(xp: Optional[str] = None):
    _check_source()
    return jsonify({"status": "ok"})


@app.route("/search", methods=["POST"])
@app.route("/<xp>/search", methods=["POST"])
def search(xp: Optional[str] = None):
    source = _check_source()
    searched_target = request.json if request.json else {}
    metrics = get_metrics(source=source, search=searched_target.get("target", None), experiment=xp)
    return jsonify(metrics)


@app.route("/query", methods=["POST"])
@app.route("/<xp>/query", methods=["POST"])
def query(xp: Optional[str] = None):
    source = _check_source()
    req = request.get_json()
    raw_resp = [t.serialize() for t in get_data(source=source,
                                                targets=req["targets"],
                                                response_type=req["targets"][0]["type"],
                                                range_from=req["range"]["from"],
                                                range_to=req["range"]["to"],
                                                experiment=xp)]
    return jsonify(raw_resp)


@app.route("/annotations", methods=["POST"])
@app.route("/tag-keys", methods=["POST"])
@app.route("/tag-values", methods=["POST"])
def annotations():
    return Response("not implemented", 404)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8900, use_reloader=False)
