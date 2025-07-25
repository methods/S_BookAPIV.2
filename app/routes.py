"""Flask application module for managing a collection of books."""

import copy

from bson import ObjectId
from flask import jsonify, request
from pymongo.errors import ConnectionFailure
from werkzeug.exceptions import HTTPException, NotFound

from app.datastore.mongo_db import get_book_collection
from app.datastore.mongo_helper import insert_book_to_mongo
from app.services.book_service import fetch_active_books, format_books_for_api
from app.utils.api_security import require_api_key
from app.utils.helper import append_hostname
from data import books


def register_routes(app):  # pylint: disable=too-many-statements
    """
    Register all Flask routes with the given app instance.

    Args:
        app (Flask): The Flask application instance to register routes on.
    """

    # ----------- POST section ------------------
    @app.route("/books", methods=["POST"])
    @require_api_key
    def add_book():
        """Function to add a new book to the collection."""

        # VALIDATION I
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 415

        new_book_data = request.json
        if not isinstance(new_book_data, dict):
            return jsonify({"error": "JSON payload must be a dictionary"}), 400

        # VALIDATION II
        required_fields = ["title", "synopsis", "author"]
        missing_fields = [
            field for field in required_fields if field not in new_book_data
        ]
        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400

        # Map field names to their expected types
        field_types = {
            "title": str,
            "synopsis": str,
            "author": str,
        }

        for field, expected_type in field_types.items():
            if not isinstance(new_book_data[field], expected_type):
                return {"error": f"Field {field} is not of type {expected_type}"}, 400

        # DATABASE OPERATIONS
        # establish connection to mongoDB
        books_collection = get_book_collection()

        # use mongoDB helper to insert/replace new book
        insert_result = insert_book_to_mongo(new_book_data, books_collection)
        # Get the new id from the insert result + str() ObjectID
        new_book_id = insert_result.inserted_id
        book_id_str = str(new_book_id)

        # Create relative links to store in the database
        links_to_store = {
            "self": f"/books/{book_id_str}",
            "reservations": f"/books/{book_id_str}/reservations",
            "reviews": f"/books/{book_id_str}/reviews",
        }

        # Update the document in MongoDB to add the links
        books_collection.update_one(
            {"_id": new_book_id}, {"$set": {"links": links_to_store}}
        )

        # PREPARE RESPONSE FROM API
        # Fetch the complete, updated document from the DB
        book_from_db = books_collection.find_one({"_id": new_book_id})

        # USE YOUR HELPER to create ABSOLUTE URLs for the client
        # Get the host from the request headers
        host = request.host_url
        # Send the host and new book_id to the helper function to generate links
        final_book_for_api = append_hostname(book_from_db, host)
        print("final_book_for_api", final_book_for_api)

        # Transform _id to id and remove the internal _id
        final_book_for_api["id"] = str(final_book_for_api["_id"])
        final_book_for_api.pop("_id", None)

        return jsonify(final_book_for_api), 201

    # ----------- GET section ------------------
    @app.route("/books", methods=["GET"])
    def get_all_books():
        """
        Retrieve all books from the database and
        return them in a JSON response
        including the total count.
        """
        try:
            raw_books = fetch_active_books()
        except ConnectionFailure:
            error_payload = {
                "error": {
                    "code": 503,
                    "name": "Service Unavailable",
                    "message": "The database service is temporarily unavailable.",
                }
            }

            return jsonify(error_payload), 503

        if not raw_books:
            return jsonify({"error": "No books found"}), 404

        # extract host from the request
        host = request.host_url.rstrip("/")

        all_formatted_books, error = format_books_for_api(raw_books, host)

        if error:
            # Return HTTP error in controller layer
            return jsonify({"error": error}), 500

        return (
            jsonify(
                {"total_count": len(all_formatted_books), "items": all_formatted_books}
            ),
            200,
        )

    @app.route("/books/<string:book_id>", methods=["GET"])
    def get_book(book_id):
        """
        Retrieve a specific book by its unique ID.
        """
        if not books:
            return jsonify({"error": "Book collection not initialized"}), 500

        # extract host from the request
        host = request.host_url

        for book in books:
            if book.get("id") == book_id and book.get("state") != "deleted":
                # copy the book
                book_copy = copy.deepcopy(book)
                book_copy.pop("state", None)
                # Add the hostname to the book_copy object and return it
                return jsonify(append_hostname(book_copy, host)), 200
        return jsonify({"error": "Book not found"}), 404

    # ----------- DELETE section ------------------
    @app.route("/books/<string:book_id>", methods=["DELETE"])
    @require_api_key
    def delete_book(book_id):
        """
        Soft delete a book by setting its state to 'deleted' or return error if not found.
        """
        if not books:
            return jsonify({"error": "Book collection not initialized"}), 500

        for book in books:
            if book.get("id") == book_id:
                book["state"] = "deleted"
                return "", 204
        return jsonify({"error": "Book not found"}), 404

    # ----------- PUT section ------------------

    @app.route("/books/<string:book_id>", methods=["PUT"])
    @require_api_key
    def update_book(book_id):
        """
        Update a book by its unique ID using JSON from the request body.
        Returns a single dictionary with the updated book's details.
        """
        if not books:
            return jsonify({"error": "Book collection not initialized"}), 500

        # check if request is json
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 415

        # check request body is valid
        request_body = request.get_json()
        if not isinstance(request_body, dict):
            return jsonify({"error": "JSON payload must be a dictionary"}), 400

        # check request body contains required fields
        required_fields = ["title", "synopsis", "author"]
        missing_fields = [
            field for field in required_fields if field not in request_body
        ]
        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400

        host = request.host_url

        # now that we have a book object that is valid, loop through books
        for book in books:
            if book.get("id") == book_id:
                # update the book values to what is in the request
                book["title"] = request.json.get("title")
                book["synopsis"] = request.json.get("synopsis")
                book["author"] = request.json.get("author")

                # Add links exists as paths only
                book["links"] = {
                    "self": f"/books/{book_id}",
                    "reservations": f"/books/{book_id}/reservations",
                    "reviews": f"/books/{book_id}/reviews",
                }
                # make a deepcopy of the modified book
                book_copy = copy.deepcopy(book)
                book_with_hostname = append_hostname(book_copy, host)
                return jsonify(book_with_hostname), 200

        return jsonify({"error": "Book not found"}), 404

    # ----------- CUSTOM ERROR HANDLERS ------------------

    @app.errorhandler(NotFound)
    def handle_not_found(e):
        """Return a custom JSON response for 404 Not Found errors."""
        return jsonify({"error": str(e)}), 404

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Return JSON for any HTTPException (401, 404, 403, etc.)
        preserving its original status code & description.
        """
        # e.code is the HTTP status code (e.g. 401)
        # e.description is the text you passed to abort()
        response = {"error": {"code": e.code, "name": e.name, "message": e.description}}
        return jsonify(response), e.code

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Return a custom JSON response for any exception."""
        return jsonify({"error": str(e)}), 500
