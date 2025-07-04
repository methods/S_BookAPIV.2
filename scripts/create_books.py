"""
Script for populating resouces to a database 
"""
from app import create_app
from app.datastore.mongo_helper import insert_book_to_mongo
from app.datastore.mongo_db import get_book_collection
from utils.db_helpers import load_books_json

# ---------------------- Book upsert helper ---------------------------
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

# ----------------------- Core population logic -----------
def run_population():
    """
    Orchestrates the process of loading and populating books.
    This function contains the core logic and is easy to test.
    
    Returns:
        str: A status message indicating success or failure.
    """
    # Setup the books collection
    books_collection = get_book_collection()
    if books_collection is None:
        return "Error: no books_collection object found"

    # Load book data from JSON file
    books_data = load_books_json()
    if books_data is None:
        return "Error: no books_data JSON found"

    # populate the DB with books_collection and books_data values
    inserted = populate_books(books_collection, books_data)

    return f"Inserted {len(inserted)} books"



# ----------------------- Entry point (runs with Flask context) -----------
def main():
    """
    Initializes the Flask application context.
    Calls the core logic and print its result
    """
    app = create_app()
    with app.app_context():
        result_message = run_population()
        print(result_message)

# Guard clause
if __name__ == "__main__":
    main()
