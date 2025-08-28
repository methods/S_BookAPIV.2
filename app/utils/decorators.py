# pylint: disable=too-many-return-statements
"""
This module provides decorators for Flask routes, including JWT authentication.
"""
import functools

import jwt
from bson.errors import InvalidId
from bson.objectid import ObjectId
from flask import current_app, g, jsonify, request, abort

from app.extensions import mongo


def require_jwt(f):
    """Protects routes by verifying JWT tokens in the
    'Authorization: Bearer <token>' header, decoding and validating the token,
    and attaching the authenticated user to the request context.
    """

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Get Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            return jsonify({"error": "Authorization header missing"}), 401

        # 2. Expect exactly: "Bearer <token>" (case-insensitive)
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Malformed Authorization header"}), 401

        token = parts[1]

        # 3. Decode & verify JWT
        try:
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET_KEY"],
                algorithms=["HS256"],
                # options={"require": ["exp", "sub"]}  # optional: force required claims
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token. Please log in again."}), 401

        # 4. Extract user id from payload
        user_id = payload.get("sub")
        if not user_id:
            return jsonify({"error": "Token missing subject (sub) claim"}), 401

        # 5. Convert to ObjectId and fetch user
        try:
            oid = ObjectId(user_id)
        except (InvalidId, TypeError):
            return jsonify({"error": "Invalid user id in token"}), 401

        # Exclude sensitive fields such as password
        user = mongo.db.users.find_one({"_id": oid}, {"password": 0})
        if not user:
            return jsonify({"error": "User not found"}), 401

        # 6. Attach safe user object to request context
        g.current_user = user

        # 7. Call original route
        return f(*args, **kwargs)

    return decorated_function


def require_admin(f):
    """A decorator that requires a user to be admin"""
    @functools.wraps(f)
    @require_jwt # ensure the user is logged in with a valid JWT
    def decorated_function(*args, **kwargs):
        user_role = g.current_user.get("role")

        if user_role != "admin":
            abort(403, description="Admin privileges required.")

        return f(*args, **kwargs)
    return decorated_function
