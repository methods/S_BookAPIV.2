"""Module containing pymongo helper functions."""

from bson.objectid import InvalidId, ObjectId
from pymongo.cursor import Cursor
from pymongo.collection import Collection


def insert_book_to_mongo(book_data, collection):
    """
    Inserts a new book document into the collection.
    MongoDB will automatically generate a unique _id for it.
    """

    result = collection.insert_one(book_data)

    # # Check the result for logging/feedback.
    if result.inserted_id:
        print(f"✅ INSERTED new book with id: {result.inserted_id}")

    return result


def upsert_book_from_file(book_data, collection):
    """
    Inserts a new book or replaces an existing one based on its 'id'.
    This is an "upsert" (update/insert) operation.

    Args:
        book_data (dict): The book document to be upserted.
        collection: The Pymongo collection object.

    Returns:
        The result of the database operation.
    """

    query_filter = {"id": book_data["id"]}

    # Use replace_one() with upsert=True.
    result = collection.replace_one(query_filter, book_data, upsert=True)

    # Check the result for logging/feedback.
    if result.upserted_id:
        print(f"✅ INSERTED new book with id: {result.upserted_id}")
    elif result.modified_count > 0:
        print(f"✅ REPLACED existing book with id: {book_data['id']}")

    return result


def find_books(collection, query_filter=None, projection=None, limit=None) -> Cursor:
    """This acts as a wrapper around pymongo's collection.find() method.

    Args:
        collection: The pymongo collection object.
        query_filter: The MongoDB query filter. Defaults to None (find all).
        projection: The fields to include/exclude. Defaults to None (all fields).
        limit: The maximum number of results to return. Defaults to None.

    Returns:
        A pymongo Cursor for the query results.
    """
    query_filter = query_filter or {}
    cursor = collection.find(query_filter, projection)
    if limit is not None and limit > 0:
        cursor = cursor.limit(limit)
    return cursor


def delete_book_by_id(book_collection: Collection, book_id: str):
    """
    Soft delete book with given id
    Returns: The original document if found and updated, otherwise None.
    """
    # Convert string ID to ObjectId
    object_id_to_update = ObjectId(book_id)

    # UPDATE operation
    update_operation = {"$set": {"state": "deleted"}}

    filter_query = {"_id": object_id_to_update, "state": {"$ne": "deleted"}}

    result = book_collection.find_one_and_update(filter_query, update_operation)

    return result

# ------ PUT helpers ------------

def validate_book_put_payload(payload: dict):
    """
    Validates the payload for a PUT request.
    A PUT must contain all required fields and no extra fields

    Returns:
        A tuple: (is_valid, error_dictionary)
        If valid, error_dictionary is None.
    """
    if not isinstance(payload, dict):
        return False, {"error": "JSON payload must be a dictionary"}

    required_fields = {"title", "synopsis", "author"}
    payload_keys = set(payload.keys())

    # Check 1: any missing fields?
    missing_fields = required_fields - payload_keys
    if missing_fields:
        # Convert the set to a list and sort it.
        sorted_missing = sorted(list(missing_fields))
        return False, {"error": f"Missing required fields: {', '.join(sorted_missing)}"}

    # Check 2: Any extra, unexpected fields?
    extra_fields = payload_keys - required_fields
    if extra_fields:
        return False, {
            "error": f"Unexpected fields provided: {', '.join(sorted(list(extra_fields)))}"
        }

    # If all checks pass:
    return True, None


def replace_book_by_id(book_collection, book_id, new_data):
    """
    Updates an ENTIRE book document in the database.
    Returns True on success, False if book not found.
    """
    try:
        object_id_to_update = ObjectId(book_id)

    except InvalidId:
        return False

    # use $set operator to update the fields OR
    # create them if they don't exist
    result = book_collection.replace_one({"_id": object_id_to_update}, new_data)

    return result.matched_count > 0
