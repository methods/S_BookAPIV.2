"""API security decorators."""
import hmac
from functools import wraps
from flask import abort, current_app, request


def require_api_key(f):
    """A decorator to protect routes with a required API key"""

    @wraps(f)
    def decorated_function(*args, **kwargs):

        # Get the real key from our application config
        expected_key = current_app.config.get("API_KEY")
        print("EXPECTED_KEY", expected_key)
        if not expected_key:
            abort(500, description="API key not configured on the server.")

        # 2. Get the provided key from the request headers.
        provided_key = request.headers.get("X-API-KEY")
        if not provided_key:
            abort(401, description="API key is missing.")

        # 3. Securely compare the provided key with the expected key
        # hmac.compare_digest is essential to prevent timing attacks
        if not hmac.compare_digest(provided_key, expected_key):
            abort(401, description="Invalid API key.")

        # If key is valid, proceed with the original function
        return f(*args, **kwargs)

    return decorated_function
