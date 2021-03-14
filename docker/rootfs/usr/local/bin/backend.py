import os
import re

import pandas as pd
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from werkzeug.exceptions import abort

app = Flask(__name__)
cors = CORS(app)


def _check_source():
    """
    checks HTTP header source is present and points to an available resource

    :return: parse HTTP header source
    """
    source = request.headers.get("source")

    if not source:
        abort(Response("HTTP header 'source' not found", 400))
    if re.match("ĥttp[s]?://", source):
        abort(Response("HTTP source not supported", 400))
    if source.startswith("s3://"):
        abort(Response("S3 source not supported", 400))

    if not os.path.exists(source):
        abort(Response("couldn't find source [{}]".format(source), 400))

    return source


def _fetch_source() -> pd.DataFrame():
    source = _check_source()
    return pd.DataFrame()


@app.route("/", methods=["GET"])
def health_check():
    _check_source()
    return jsonify({"status": "ok"})


@app.route("/search", methods=["POST"])
def search():
    source = _fetch_source()
    return jsonify(["TODO"])


@app.route("/query", methods=["POST"])
def query():
    source = _fetch_source()
    req = request.get_json()
    targets = req["targets"]
    range_from = req["range"]["from"]
    range_to = req["range"]["to"]
    # example
    data = [
        {
            "target": req['targets'][0]['target'],
            "datapoints": [
                [861, convert_to_time_ms(req['range']['from'])],
                [767, convert_to_time_ms(req['range']['to'])]
            ]
        }
    ]


@app.route('/annotations', methods=['POST'])
@app.route('/tag-keys', methods=['POST'])
@app.route('/tag-values', methods=['POST'])
def annotations():
    return Response("not implemented", 404)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8900, use_reloader=False)
