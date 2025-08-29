"""Routes for /books/<id>/reservations endpoint"""

import datetime
import logging

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, g, jsonify, url_for

from app.extensions import mongo
from app.utils.decorators import require_jwt, require_admin

reservations_bp = Blueprint(
    "reservations_bp", __name__, url_prefix="/books/<book_id_str>"
)


@reservations_bp.route("/reservations", methods=["POST"])
@require_jwt
def create_reservation(book_id_str):
    """
    This POST endpoint lets an authenticated user reserve a book by its ID.
    It validates the ID, checks book availability, 
    prevents duplicate reservations, 
    creates the reservation, and returns its details.
    """

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

    #  ---------- VALIDATION 2 - Check for existing reservation
    # A user should not be able to reserve the same book more than once.
    existing_reservation = mongo.db.reservations.find_one(
        {"book_id": book_id, "user_id": current_user_id}
    )
    if existing_reservation:
        return jsonify({"error": "You have already reserved this book"}), 409

    #    2. DOCUMENT CREATION
    reservation_doc = {
        "book_id": book_id,
        "state": "reserved",
        "user_id": current_user_id,
        "reservation_date": datetime.datetime.now(datetime.UTC),
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
            "self": url_for(
                ".create_reservation", book_id_str=str(book_id), _external=True
            ),
            "book": url_for("get_book", book_id=str(book_id), _external=True),
        },
        "reservation_date": reservation_doc["reservation_date"].isoformat(),
    }

    return jsonify(response_data), 201


@reservations_bp.route("/reservations", methods=["GET"])
@require_admin
def get_reservations_for_book_id(book_id_str):
    """
    Retrieves all reservations for a specific book.
    Accessible only by users with the 'admin' role.
    """
    # Validate the book_id format
    try:
        oid = ObjectId(book_id_str)
    except (InvalidId, TypeError):
        return jsonify({"error": "Invalid Book ID"}), 400

    # Check if book exists
    book = mongo.db.books.find_one({"_id": oid})
    if not book:
        return "book not found", 404, {"Content-Type": "text/plain"}

    # Fetch reservations for the given book_id
    reservations_cursor = mongo.db.reservations.find({"book_id": oid})

    items = []
    for r in reservations_cursor:
        # For each reservation, fetch the associated user's details
        user = mongo.db.users.find_one({"_id": r["user_id"]})

        # Skip if the user for a reservation is not found, to avoid errors
        if not user:
            logging.warning(
                "Data integrity issue: Reservation '%s' references a non-existent user_id '%s'. Skipping.", # pylint: disable=line-too-long
                r['_id'], r['user_id']
            )
            continue

        # Build the item object according to spec
        reservation_item = {
            "id": str(r["_id"]),
            "state": r.get("state", "UNKNOWN"),  # Use .get() for safety
            "user": {
                    "forenames": user.get("forenames"),
                    "surname": user.get("surname")
                },
            "book_id": str(r["book_id"]),
            "links": {
                 "self": url_for(
                    '.get_reservations_for_book_id',
                    reservation_id=str(r["_id"]),
                    _external=True),
                "book": url_for(
                    'get_book',
                    book_id=str(r["book_id"]),
                    _external=True)
            }
        }

        items.append(reservation_item)

    # Construct the final response body
    response_body = {
        "total_count": len(items),
        "items": items
    }

    return jsonify(response_body), 200
