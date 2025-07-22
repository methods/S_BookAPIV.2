"""API security decorators."""

import hmac
from functools import wraps

from flask import abort, current_app, request


def log_unauthorized_access():
    """
    Helper function to log a warning for unauthorized access attempts with IP and path info.
    """
    current_app.logger.warning(
        f"Unauthorized access attempt: IP={request.remote_addr}, path={request.path}"
    )


def require_api_key(f):
    """A decorator to protect routes with a required API key"""

    @wraps(f)
    def decorated_function(*args, **kwargs):

        expected_key = current_app.config.get("API_KEY")

        if not expected_key:
            # Secure logging — don't leak keys
            log_unauthorized_access()

            abort(500, description="API key not configured on the server.")

        provided_key = request.headers.get("X-API-KEY")
        if not provided_key:
            # Secure logging — don't leak keys
            log_unauthorized_access()
            abort(401, description="API key is missing.")

        # Securely compare the provided key with the expected key
        if not hmac.compare_digest(provided_key, expected_key):
            # Secure logging — don't leak keys
            log_unauthorized_access()
            abort(401, description="Invalid API key.")

        # If key is valid, proceed with the original function
        return f(*args, **kwargs)

    return decorated_function
