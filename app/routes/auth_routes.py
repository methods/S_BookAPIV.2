"""Routes for authorrization for the JWT upgrade"""

from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/books")


@auth_bp.route("auth/register", methods=["POST"])
def register_user():
    """Function that takes user information
    Verfies it is not a duplicate email
    SENDS it to mongoDB to be stored
    """
    return "User registered", 201
