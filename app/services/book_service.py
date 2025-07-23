from app.datastore.mongo_db import get_book_collection
from app.datastore.mongo_helper import find_books

def fetch_active_books_cursor():
    """Fetches a cursor for all non-deleted books from the database."""

    collection = get_book_collection()
    query_filter = {"state": {"ne": "deleted"}}  # Only non-deleted books

    return find_books(collection, query_filter=query_filter)
