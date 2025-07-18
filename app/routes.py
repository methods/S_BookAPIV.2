"""Flask application module for managing a collection of books."""

import copy
import uuid

from flask import jsonify, request
from werkzeug.exceptions import HTTPException, NotFound

from app.datastore.mongo_db import get_book_collection
from app.datastore.mongo_helper import insert_book_to_mongo
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
        # check if request is json
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 415

        new_book = request.json
        if not isinstance(new_book, dict):
            return jsonify({"error": "JSON payload must be a dictionary"}), 400

        # create UUID and add it to the new_book object
        new_book_id = str(uuid.uuid4())
        new_book["id"] = new_book_id

        # validation
        required_fields = ["title", "synopsis", "author"]
        missing_fields = [field for field in required_fields if field not in new_book]
        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400

        new_book["links"] = {
            "self": f"/books/{new_book_id}",
            "reservations": f"/books/{new_book_id}/reservations",
            "reviews": f"/books/{new_book_id}/reviews",
        }

        # Map field names to their expected types
        field_types = {
            "id": str,
            "title": str,
            "synopsis": str,
            "author": str,
            "links": dict,
        }

        for field, expected_type in field_types.items():
            if not isinstance(new_book[field], expected_type):
                return {"error": f"Field {field} is not of type {expected_type}"}, 400

        # use helper function
        books_collection = get_book_collection()
        # check if mongoDB connected??
        insert_book_to_mongo(new_book, books_collection)

        # Get the host from the request headers
        host = request.host_url
        # Send the host and new book_id to the helper function to generate links
        book_for_response = append_hostname(new_book, host)
        print("book_for_response", book_for_response)

        # Remove MongoDB's ObjectID value
        book_for_response.pop("_id", None)

        return jsonify(book_for_response), 201

    # ----------- GET section ------------------
    @app.route("/books", methods=["GET"])
    def get_all_books():
        """
        Retrieve all books from the database and
        return them in a JSON response
        including the total count.
        """
        if not books:
            return jsonify({"error": "No books found"}), 404

        all_books = []
        # extract host from the request
        host = request.host_url

        for book in books:
            # check if the book has the "deleted" state
            if book.get("state") != "deleted":
                # Remove state unless it's "deleted", then append
                book_copy = copy.deepcopy(book)
                book_copy.pop("state", None)
                book_with_hostname = append_hostname(book_copy, host)
                all_books.append(book_with_hostname)

        # validation
        required_fields = ["id", "title", "synopsis", "author", "links"]
        missing_fields_info = []

        for book in all_books:
            missing_fields = [field for field in required_fields if field not in book]
            if missing_fields:
                missing_fields_info.append(
                    {"book": book, "missing_fields": missing_fields}
                )

        if missing_fields_info:
            error_message = "Missing required fields:\n"
            for info in missing_fields_info:
                error_message += f"Missing fields: {', '.join(info['missing_fields'])} in {info['book']}. \n"  # pylint: disable=line-too-long

            print(error_message)
            return jsonify({"error": error_message}), 500

        count_books = len(all_books)
        response_data = {"total_count": count_books, "items": all_books}

        return jsonify(response_data), 200

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

    @app.errorhandler(NotFound)
    def handle_not_found(e):
        """Return a custom JSON response for 404 Not Found errors."""
        return jsonify({"error": str(e)}), 404

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """
        Return JSON for any HTTPException (401, 404, 403, etc.)
        preserving its original status code & description.
        """
        # e.code is the HTTP status code (e.g. 401)
        # e.description is the text you passed to abort()
        response = {"error": {"code": e.code, "message": e.description}}
        return jsonify(response), e.code

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Return a custom JSON response for any exception."""
        return jsonify({"error": str(e)}), 500
