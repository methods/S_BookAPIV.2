"""Module containing pymongo helper functions."""

from bson.objectid import ObjectId, InvalidId
from pymongo.cursor import Cursor


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


def delete_book_by_id(book_collection: dict, book_id: str):
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


def update_book_by_id(book_collection, book_id, data):

    """Updates an ENTIRE book document in the database"""
    try:
        # convert string ID to ObjectId
        object_id_to_update = ObjectId(book_id)

    except InvalidId:
        return None

    # use $set operator to update the fields OR
    # create them if they don't exist
    result = book_collection.update_one(
        {'_id': object_id_to_update},
        {'$set': data}
    )

    return result.matched_count
