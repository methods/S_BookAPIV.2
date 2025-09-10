"""..."""

from bson import ObjectId

from app.extensions import mongo


def count_reservations_for_book(book_id: ObjectId) -> int:
    """Counts the total number of reservations for a given book ID"""
    return mongo.db.reservations.count_documents({"book_id": book_id})
