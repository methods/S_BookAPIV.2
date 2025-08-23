"""Routes for /books/<id>/reservations endpoint"""
import datetime

from flask import Blueprint, jsonify, url_for, g
from bson import ObjectId
from bson.errors import InvalidId
from app.extensions import mongo
from app.utils.decorators import require_jwt

reservations_bp = Blueprint("reservations_bp", __name__, url_prefix="/books/<book_id_str>")

@reservations_bp.route("/reservations", methods=["POST"])
@require_jwt
def create_reservation(book_id_str):
    """..."""

    # ---------- VALIDATION 1 - check payload has valid id - mongoDB id shape

    try:
        # convert string to an ObjectId
        book_id = ObjectId(book_id_str)
    except (InvalidId, TypeError):
        return jsonify({"error": "Invalid Book ID"}), 400

    # Check if book exists or throw 404
    book = mongo.db.books.find_one({"_id": book_id})
    if not book:
        return jsonify({"error": "Book not found"}), 404

    # Get the current user directly from Flask's 'g'
    current_user_id = g.current_user["_id"]

#    2. DOCUMENT CREATION
    reservation_doc = {
        "book_id": book_id,
        "state": "reserved",
        "user_id": current_user_id,
        "reservation_date": datetime.datetime.now(datetime.UTC)
    }

    # Insert new reservation to MongoDb 'reservation' collection
    result = mongo.db.reservations.insert_one(reservation_doc)
    new_reservation_id = result.inserted_id

    # 3. RESPONSE PREP
    response_data = {
        "id": str(new_reservation_id),
        "state": reservation_doc["state"],
        "user_id": reservation_doc["user_id"],
        "book_id": str(reservation_doc["book_id"]),
        "links": {
            "self": url_for(".create_reservation", book_id_str=str(book_id), _external=True),
            "book": url_for("get_book", book_id=str(book_id), _external=True)
        },
        "reservation_date": reservation_doc["reservation_date"].isoformat()
    }

    return jsonify(response_data), 201
