from flask import request, abort, jsonify, g
from functools import wraps

def check_app_json():
    """
        Check that the request is a valid application/json and return the body content
    """
    if not request.content_type.startswith('application/json'):
        abort(400)
    data = request.get_json()
    if (not data):
        abort(400)
    return data


def appjson_required(f):
    """
    Set context g.request_data variable with json request content
    Args:
        f: wrapped function

    Returns:

    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            assert request.headers['Content-Type'].startswith('application/json')
            g.request_data = request.get_json()
        except:
            return jsonify({'error': 'invalid_request', 'error_description': 'Invalid request, a valid application/json is expected'}), 400
        return f(*args, **kwargs)
    return wrapper