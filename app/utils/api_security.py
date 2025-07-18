"""API security decorators."""

from functools import wraps
from flask import request, abort, current_app

def require_api_key(f):
    """A decorator to protect routes with a required API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for the key in the request headers.
        provided_key = request.headers.get("X-API-KEY")
        print("PROVIDED_KEY", provided_key)

        # Get the real key from our application config
        expected_key = current_app.config.get('API_KEY')
        print("EXPECTED_KEY", expected_key)

        if not provided_key or provided_key != expected_key:
            abort(401, description="Invalid or missing API Key.")

        # If key is valid, proceed with the original function
        return f(*args, **kwargs)
    return decorated_function
