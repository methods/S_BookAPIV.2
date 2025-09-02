"""
This script completely clears all reservations from the configured MongoDB collection.
"""
import sys
from pymongo.errors import ConnectionFailure
from app import create_app
from app.datastore.mongo_db import get_reservation_collection

def delete_all_reservations(collection):
    """
    Delete all documents from the reservations collection.

    Args:
        collection: The MongoDB collection object for reservations.

    Returns:
        int: The number of documents deleted.
    """
    print("Attempting to delete all documents from the 'reservations' collection...")
    # get reservations collection
    result = collection.delete_many({})
    return result.deleted_count


def main():
    """
    Starts the Flask app context, connects to MongoDB, and 
    Deletes all documents in the reservations collection.

    Returns:
        int: 0 on success, 1 on failure.
    """
    app = create_app()
    with app.app_context():
        try:
            reservations_collection = get_reservation_collection()

            num_deleted = delete_all_reservations(reservations_collection)

            if num_deleted > 0:
                print(f"✅ Success: Removed {num_deleted} reservation(s).")
            else:
                print("ℹ️ Info: The collection was already empty. No reservations were deleted.")
            # Return success code
            return 0
        except ConnectionFailure as e:
            print("❌ ERROR: Could not connect to MongoDB.", file=sys.stderr)
            print(f"Details: {e}", file=sys.stderr)

            # Return the failure code.
            return 1


if __name__ == "__main__":
    # A confirmation step is crucial for destructive scripts.
    confirm = input(
        "⚠️  This will delete ALL reservations from the database. Are you sure? (y/N) "
    )
    if confirm.lower() != "y":
        print("Operation cancelled.")
        sys.exit(0)

    # Call main and get the exit code it determined.
    EXIT_CODE = main()

    # Use the returned code to exit the script.
    # This cleanly separates the script's logic from its execution.
    sys.exit(EXIT_CODE)
