"""Utility functions to interact with a MongoDB collection"""

from flask import current_app
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from app.extensions import mongo


def get_book_collection():
    """
    Initialize the mongoDB connection
    Use current_app to get global flask instance context
    """
    try:
        client = MongoClient(
            current_app.config["MONGO_URI"], serverSelectionTimeoutMS=5000
        )

        db = client[current_app.config["DB_NAME"]]
        books_collection = db[current_app.config["COLLECTION_NAME"]]
        return books_collection
    except ConnectionFailure as e:

        raise ConnectionFailure(f"Could not connect to MongoDB: {str(e)}") from e


def get_reservation_collection():
    """Returns the PyMongo collection for reservations."""
    reservations_collection = mongo.db.reservations

    return reservations_collection
