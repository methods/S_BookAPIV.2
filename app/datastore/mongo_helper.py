"""Module containing pymongo helper functions."""

from pymongo.cursor import Cursor


def insert_book_to_mongo(book_data, collection):
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
    #    - Parameter 1: The filter to find the document to replace.
    #    - Parameter 2: The new document that will replace the old one.
    #    - Parameter 3: upsert=True tells MongoDB:
    #      - "If you find a document matching the filter, REPLACE it with the new data."
    #      - "If you DON'T find a document, INSERT the new data as a new document."
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
        filter: The MongoDB query filter. Defaults to None (find all).
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
