"""
This script completely clears all books from the configured MongoDB collection.
It is a destructive and irreversible operation.
"""

from app import create_app
from app.datastore.mongo_db import get_book_collection

def delete_all_books(collection):
    """Deletes all documents from the given collection."""

    print("Attempting to delete all documents from the books collection...")

    # The delete_many({}) operation finds all documents and deletes them.
    # It returns a DeleteResult object, which contains useful information.
    delete_result = collection.delete_many({})
    print(f"Delete operation completed. Documents affected: {delete_result.deleted_count}.")

    # Return the count of deleted documents.
    return delete_result.deleted_count

# The "manager" or "runner" function.
# Its job is to connect the Flask app's config to the pure logic.
def main():
    """
    Starts the Flask app context and deletes all documents from MongoDB.
    Serves as the entry point for the cleanup operation.
    """

    app = create_app()

    # The app_context makes app.config available.
    with app.app_context():
        collection = get_book_collection()

        num_deleted = delete_all_books(collection)

        if num_deleted > 0:
            print(f"✅ Success: Removed {num_deleted} existing document(s).")
        else:
            print("ℹ️ Info: The collection was already empty. No documents were deleted.")


if __name__ == "__main__":
    main()
