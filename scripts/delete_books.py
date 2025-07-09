"""
This script completely clears all books from the configured MongoDB collection.
It is a destructive and irreversible operation.

Exits with status code 0 on success (including if the collection was already empty).
Exits with status code 1 on failure (e.g., cannot connect to the database).
"""

import sys
from pymongo.errors import ConnectionFailure
from app import create_app
from app.datastore.mongo_db import get_book_collection


def delete_all_books(collection):
    """Delete all documents from the given collection.

    Args:
        collection: A MongoDB collection object.

    Returns:
        int: The number of documents deleted.
    """

    print("Attempting to delete all documents from the books collection...")
    # It returns a DeleteResult object, which contains useful information.
    delete_result = collection.delete_many({})
    print(
        f"Delete operation completed. Documents affected: {delete_result.deleted_count}."
    )
    return delete_result.deleted_count


# The "manager" or "runner" function.
# Its job is to connect the Flask app's config to the pure logic.
def main():
    """
    Starts the Flask app context, connects to MongoDB, and deletes all
    documents in the books collection.
    
    Returns:
        int: 0 on success, 1 on failure.
    """

    app = create_app()

    # The app_context makes app.config available.
    with app.app_context():
        try:
            collection = get_book_collection()

            num_deleted = delete_all_books(collection)

            if num_deleted > 0:
                print(f"✅ Success: Removed {num_deleted} existing document(s).")
            else:
                print(
                    "ℹ️ Info: The collection was already empty. No documents were deleted."
                )
            return 0
        except ConnectionFailure as e:
            # This is a critical failure. The script could not do its job.
            # Printing to sys.stderr is best practice for error messages.
            print("❌ ERROR: Could not connect to MongoDB.", file=sys.stderr)
            print("Please ensure the database is running and accessible.", file=sys.stderr)
            print(f"Details: {e}", file=sys.stderr)

            # Return the failure code.
            return 1


if __name__ == "__main__":
    # A confirmation step is crucial for destructive scripts.
    confirm = input(
        "⚠️  This will delete ALL books from the database. Are you sure? (y/N) "
    )
    if confirm.lower() != "y":
        print("Operation cancelled.")
        sys.exit(0)

    # Call main and get the exit code it determined.
    EXIT_CODE = main()

    # Use the returned code to exit the script.
    # This cleanly separates the script's logic from its execution.
    sys.exit(EXIT_CODE)
