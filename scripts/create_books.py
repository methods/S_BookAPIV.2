"""
Script for populating resouces to a database 
"""
from app.datastore.mongo_helper import insert_book_to_mongo
from app.datastore.mongo_db import get_book_collection
from utils.db_helpers import load_books_json

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

# ----------------------- Main function to upsert to database -----------
def main():
    """
    Orchestrates the process of populating the books collection in the database.
    """
    # Setup the books collection
    books_collection = get_book_collection()
    # Load book data from JSON file
    books_data = load_books_json()
    inserted = populate_books(books_collection, books_data)

    print(f"Inserted {len(inserted)} books")

# Guard clause
if __name__ == "__main__":
    main()
