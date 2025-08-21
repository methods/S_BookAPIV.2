"""Routes for /books/<id>/reservations endpoint"""
import datetime

from flask import Blueprint, jsonify, request, url_for
from bson import ObjectId
from bson.errors import InvalidId
from werkzeug.exceptions import BadRequest
from app.extensions import mongo


reservations_bp = Blueprint("reservations_bp", __name__, url_prefix="/books/<book_id_str>")

@reservations_bp.route("/reservations", methods=["POST"])
def create_reservation(book_id_str):
    """..."""

    # ---------- VALIDATION 1 - check payload has valid id - mongoDB id shape
    if not book_id_str:
        return jsonify({"error": "Book ID is required"}), 400

    try:
        # convert string to an ObjectId
        book_id = ObjectId(book_id_str)
    except (InvalidId, TypeError):
        return jsonify({"error": "Invalid Book ID"}), 400

    # Check if book exists or throw 404
    book = mongo.db.books.find_one({"_id": book_id})
    if not book:
        return jsonify({"error": "Book not found"}), 404

    # --------- VALIDATION 2
    # check payload exists & is JSON
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Request body cannot be empty"}), 400

        errors = {}
        if "forenames" not in data or not isinstance(data.get("forenames"), str):
            errors["forenames"] = "forenames is required and must be a string"
        if "surname" not in data or not isinstance(data.get("surname"), str):
            errors["surname"] = "surname is required and must be a string"
        if errors:
            return jsonify({"error": "Validation failed", "messages": errors}), 400

        # extract data from payload
        forenames = data.get("forenames")
        surname = data.get("surname")

        # Clean and split the forenames string into a list of words
        forenames_list = forenames.strip().split()

        firstname = forenames_list[0]
        middle_names = ' '.join(forenames_list[1:])


    except BadRequest:
        return jsonify({"message": "Invalid JSON format"}), 400


    # 2. DOCUMENT CREATION
    reservation_doc = {
        "book_id": book_id,
        "state": "reserved",
        "user": {
            "forenames": firstname,
            "middlenames": middle_names,
            "surname": surname
        },
        # Add time reservation was made
        "reservation_date": datetime.datetime.utcnow()
    }

    # Insert new reservation to MongoDb 'reservation' collection
    result = mongo.db.reservations.insert_one(reservation_doc)
    new_reservation_id = result.inserted_id


    # 3. RESPONSE PREP
    response_data = {
        "id": str(new_reservation_id),
        "state": reservation_doc["state"],
        "user": reservation_doc["user"],
        "book_id": str(reservation_doc["book_id"]),
        "links": {
            # HATEOAS-style links: use url_for so routes stay dynamic and consistent.
            # Note: the argument name passed to url_for must match the parameter
            # expected by the target view function (e.g. "book_id_str").
            "self": url_for(".create_reservation", book_id_str=str(book_id), _external=True),
            "book": url_for("get_book", book_id=str(book_id), _external=True)
        },
        "reservation_doc": reservation_doc["reservation_date"].isoformat()
    }

    return jsonify(response_data), 201
