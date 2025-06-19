from flask import current_app
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


def get_book_collection():
    """
    Initialize the mongoDB connection
    Use current_app to get global flask instance context
    """
    try:
        client = MongoClient(current_app.config['MONGO_URI'], serverSelectionTimeoutMS=5000)
        # Check the status of the server, will fail if server is down
        db = client[current_app.config['DB_NAME']]
        books_collection = db[current_app.config['COLLECTION_NAME']]
        return books_collection
    except ConnectionFailure as e:
        # Handle the connection error and return error information
        raise ConnectionFailure(f'Could not connect to MongoDB: {str(e)}') from e