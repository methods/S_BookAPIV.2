"""
Script for populating resouces to a database 
"""
from pymongo import MongoClient
from app import create_app


def delete_all_books(collection):
    """Deletes all documents from the given collection."""
    # {} filter: match all documents; delete_many({}) deletes them all (preserves indexes, irreversible, returns DeleteResult) # pylint: disable=line-too-long
    collection.delete_many({})
    print("Database has been dropped.")

# The "manager" or "runner" function.
# Its job is to connect the Flask app's config to the pure logic.
def main():
    """
    Starts the Flask app context, connects to MongoDB, 
    and deletes all documents in the collection.
    This function acts as the entry point for managing 
    the cleanup operation via the Flask app context.
    """
    app = create_app()

    # The app_context makes app.config available.
    with app.app_context():
        # get config values from app and save to variables
        mongo_connection_uri = app.config['MONGO_URI']
        db_name = app.config['DB_NAME']
        collection_name = app.config['COLLECTION_NAME']

        print(f"Connecting to database '{db_name}'...")
        client = MongoClient(mongo_connection_uri)
        db = client[db_name]
        collection = db[collection_name]

        delete_all_books(collection)

if __name__ == "__main__":
    main()
