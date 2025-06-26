"""
Script for populating resouces to a database 
"""
from app.datastore.mongo_helper import insert_book_to_mongo

# ---------------------------- Helper function ---------------------------
def populate_books(collection, data):
    """
    Upserts a list of books into a collection using a bulk write operation.
    Args:
        collection: MongoDB collection instance.
        data (list): List of dictionaries representing books.

    Returns:
        list: List of books that were inserted.
    """
    inserted_books_list = []
    for book in data:
        insert_book_to_mongo(book, collection)
        inserted_books_list.append(book)

    return inserted_books_list
