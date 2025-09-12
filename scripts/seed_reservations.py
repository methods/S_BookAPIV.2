# pylint: disable=too-many-locals
"""
Script for populating reservations to a database
"""

import json
import os
import sys

from flask import jsonify
from pymongo.errors import PyMongoError

# Import MongoDB helper functions
from app.datastore.mongo_db import (get_book_collection,
                                    get_reservation_collection,
                                    get_users_collection)


# upload sample data json to be used
def load_reservations_json():
    """Loads the reservation seed data from the JSON file
    located at scripts/test_data/sample_reservations.json
    Returns:
        list: List of reservation dictionaries
    """
    try:
        script_dir = os.path.dirname(__file__)
        data_path = os.path.join(script_dir, "test_data/sample_reservations.json")

        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Data file not found at '{data_path}'.", file=sys.stderr)
        return None
    except json.JSONDecodeError:
        print(
            f"ERROR: Could not decode JSON from '{data_path}'. Check for syntax.",
            file=sys.stderr,
        )  # pylint: disable=line-too-long
        return None


def run_reservation_population():
    """
    Populates the reservations collection in the database using sample data from a JSON file.
    This function:
        - Loads books, reservations and users collections from the database.
        - Creates a mapping from book titles to their database IDs.
        - Creates a mapping from user emails to their database IDs.
        - Loads reservation seed data from a JSON file.
        - Inserts new reservations or updates existing ones based on the data.
        - Handles errors related to database access and data loading.
    Returns:
        tuple or Response:
            - On success or handled error, returns a tuple (success: bool, message: str).
            - If required collections cannot be loaded, returns a Flask Response and status code.
    Exceptions:
        Does not raise exceptions directly; errors are caught and returned as part of the result.
    """
    # 1. need to get the collections
    books_collection = get_book_collection()
    reservations_collection = get_reservation_collection()
    users_collection = get_users_collection()

    if books_collection is None or reservations_collection is None:
        return jsonify({"error": "Required collections could not be loaded."}), 404

    # 3. Build the two lookup maps
    print("Fetching existing books to create a title-to-ID map...")
    print("Fetching existing users to create an email-to-ID map...")
    try:
        # --- Create the book lookup map ---
        # collection.find(filter, projection: 1=include, 0=exclude )
        book_cursor = books_collection.find({}, {"_id": 1, "title": 1})
        # MAP book title to book id
        book_id_map = {book["title"]: book["_id"] for book in book_cursor}

        if not book_id_map:
            return (
                True,
                "Warning: No books found in the database. Cannot create reservations.",
            )

        # --- Create the user lookup map ---
        user_cursor = users_collection.find({}, {"_id": 1, "email": 1})
        # MAP user email to user id
        user_id_map = {user["email"]: user["_id"] for user in user_cursor}

        if not user_id_map:
            return (
                True,
                "Warning: No users found in the database. Cannot create reservations.",
            )

    except PyMongoError as e:
        return (False, f"ERROR: Failed to fetch data from database: {e}")

    # ------------------------------------------------------------------------------------------
    # 4. Load the new reservations data from JSON file
    reservations_to_create = load_reservations_json()

    if reservations_to_create is None:
        return (False, "Failed to load reservation data.")

    # ------------------------------------------------------------------------------------------
    # 5. Process and insert each reservation
    # Initialize count for created and updated
    print("Processing and inserting/updating reservations...")
    created_count = 0
    updated_count = 0

    # Loop through uploaded reservations JSON list
    for res_data in reservations_to_create:
        # Take the book title value and the user_email from the json
        # look it up in our maps created above
        book_title = res_data.get("book_title")
        user_email = res_data.get("user_email")

        book_id = book_id_map.get(book_title)
        user_id = user_id_map.get(user_email)

        if not book_id or not user_id:
            print(
                f"WARNING: Skipping reservation because book '{book_title}' or user '{user_email} was not found."  # pylint: disable=line-too-long
            )
            continue

        # add book_id (the real Mongo _id) to the reservation_doc object
        reservation_doc = {
            "user_id": user_id,
            "book_id": book_id,
            "state": res_data["state"],
            "surname": res_data["surname"],
            "forenames": res_data["forenames"],
        }

        # query to find which document we want to update
        filter_query = {
            "user_id": user_id,
            "book_id": book_id,
        }

        # $set = mongodb update operator
        # replace if exists and upsert if it doesnt exist
        update_query = {"$set": reservation_doc}

        # the update call
        try:
            result = reservations_collection.update_one(
                filter_query,  # dict: criteria to find the target document(s)
                update_query,  # dict: update operators ($set, $inc, etc.) describing the changes
                upsert=True,  # bool: if no document matches filter, insert a new one (merge filter + update) # pylint: disable=line-too-long
            )

            if result.upserted_id:
                created_count += 1
            elif result.matched_count > 0:
                updated_count += 1
        except PyMongoError as e:
            return (
                False,
                f"ERROR: Failed to upsert reservation for user '{user_email}': {e}",
            )  # pylint: disable=line-too-long

    summary = f"Successfully created {created_count} and updated {updated_count} reservations."
    return (True, summary)


if __name__ == "__main__":
    from app import \
        create_app  # Import the create_app function from your app module

    app = create_app()  # create the Flask app
    with app.app_context():  # activate app context
        success, message = run_reservation_population()
        print(message)
        if not success:
            sys.exit(1)  # Exit with an error code if something failed
