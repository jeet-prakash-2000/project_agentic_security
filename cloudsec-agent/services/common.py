import json
import azure.functions as func


def success_response(data):

    return func.HttpResponse(
        json.dumps(data, default=str),
        status_code=200,
        mimetype="application/json"
    )


def error_response(message, status_code=500):

    return func.HttpResponse(
        json.dumps({
            "status": "failed",
            "message": str(message)
        }),
        status_code=status_code,
        mimetype="application/json"
    )


def get_body(req):

    try:
        return req.get_json()

    except Exception:
        raise ValueError(
            "Invalid JSON payload"
        )