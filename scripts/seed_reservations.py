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
                                    get_reservation_collection)


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
    """..."""
    # 1. need to get the collections
    books_collection = get_book_collection()
    reservations_collection = get_reservation_collection()

    if books_collection is None or reservations_collection is None:
        return jsonify({"error": "Required collections could not be loaded."}), 404

    # 3. Build a Python dictionary
    # Create a lookup map from book title to its DB _id
    print("Fetching existing books to create a title-to-ID map...")
    try:
        # collection.find(filter, projection: 1=include, 0=exclude )
        book_cursor = books_collection.find({}, {"_id": 1, "title": 1})
        book_id_map = {book["title"]: book["_id"] for book in book_cursor}
        print(book_id_map)
        if not book_id_map:
            return (
                True,
                "Warning: No books found in the database. Cannot create reservations.",
            )
    except PyMongoError as e:
        return (False, f"ERROR: Failed to fetch books from database: {e}")

    # 4. Load the new reservations data from JSON - load_reservation_json helper function
    reservations_to_create = load_reservations_json()
    print("reservations_to_create: ", reservations_to_create)
    if reservations_to_create is None:
        return (False, "Failed to load reservation data.")

    # 5. Process and insert each reservation
    # initilize count for created and updated
    print("Processing and inserting/updating reservations...")
    created_count = 0
    updated_count = 0

    # Loop through uploaded reservations JSON list
    for res_data in reservations_to_create:
        # Take the book title value from the json
        # look it up in the dictonary
        book_title = res_data.get("book_title")
        book_id = book_id_map.get(book_title)

        if not book_id:
            print(
                f"WARNING: Skipping reservation because book '{book_title}' was not found."
            )
            continue

        # add book_id (the real Mongo _id) to the reservation_doc object
        reservation_doc = {
            "user_id": res_data["user_id"],
            "book_id": book_id,
            "state": res_data["state"],
        }

        # query to find which document we want to update
        filter_query = {
            "user_id": reservation_doc["user_id"],
            "book_id": reservation_doc["book_id"],
        }

        # $set = mongodb update operator
        # replace if exists and upsert it doesnt exist
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
                f"ERROR: Failed to upsert reservation for user '{res_data['user_id']}': {e}",
            )  # pylint: disable=line-too-long

    # success placeholder
    return jsonify({"status": "success", "message": "Collections loaded."}), 200


if __name__ == "__main__":
    print(load_reservations_json())
