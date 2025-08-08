# pylint: disable=cyclic-import
"""Routes for authorization for the JWT upgrade"""

import bcrypt
from email_validator import EmailNotValidError, validate_email
from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest

from app.extensions import mongo

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
    # Easy access with Flask_PyMongo's 'mongo'
    if mongo.db.users.find_one({"email": email}):
        return jsonify({"message": "Email is already registered"}), 409

    # Password Hashing
    # Generate a salt and hash the password
    # result is a byte object representing the final hash
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    # Database Insertion
    user_id = mongo.db.users.insert_one(
        {
            "email": email,
            # The hash is stored as a string in the DB
            "password_hash": hashed_password.decode("utf-8"),
        }
    ).inserted_id
    print(user_id)

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
