# pylint: disable=cyclic-import
"""Routes for authorization for the JWT upgrade"""

import datetime

import jwt
from email_validator import EmailNotValidError, validate_email
from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import BadRequest

from app.extensions import bcrypt, mongo

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register_user():
    """
    Registers a new user.
    Takes a JSON payload with "email" and "password".
    It verfies it is not a duplicate email,
    Hashes the password and stores the new user in the database.
    """

    # VALIDATION the incoming data/request payload
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Request body cannot be empty"}), 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400

        # email-validator
        try:
            valid = validate_email(email, check_deliverability=False)

            # use the normalized email for all subsequent operations
            email = valid.normalized
        except EmailNotValidError as e:
            return jsonify({"message": str(e)}), 400

    except BadRequest:
        return jsonify({"message": "Invalid JSON format"}), 400

    # Check for Duplicate User
    if mongo.db.users.find_one({"email": email}):
        return jsonify({"message": "Email is already registered"}), 409

    # Password Hashing
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    # Database Insertion
    user_id = mongo.db.users.insert_one(
        {
            "email": email,
            # The hash is stored as a string in the DB
            "password": hashed_password,
            "role": "user", # all users asssigned a default 'user' role
        }
    ).inserted_id

    # Prepare response
    return (
        jsonify(
            {
                "message": "User registered successfully",
                "user": {"id": str(user_id), "email": email},
            }
        ),
        201,
    )


# ----- LOGIN -------
@auth_bp.route("/login", methods=["POST"])
def login_user():
    """Authenticates a user and returns a JWT"""
    # 1. Get the user's credentials from the request body
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password are required"}), 400

    email = data.get("email")
    password = data.get("password")

    # 2. Find the user in the DB
    user = mongo.db.users.find_one({"email": email})

    # 3. Verify the user and password
    if not user or not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    # 4. Generate the JWT payload
    payload = {
        "sub": str(user["_id"]),  # sub (subject)- standard claim for user ID
        "iat": datetime.datetime.now(
            datetime.UTC
        ),  # iat (issued at)- when token was created
        "exp": datetime.datetime.now(datetime.UTC)
        + datetime.timedelta(hours=24),  # expiration
    }

    # 5. Encode the token with our app's JWT_SECRET_KEY
    try:
        token = jwt.encode(
            payload,
            current_app.config["JWT_SECRET_KEY"],
            algorithm="HS256",  # the standard signing algorithm
        )
        return jsonify({"token": token}), 200
    except jwt.PyJWTError:
        return jsonify({"error": "Token generation failed"}), 500
