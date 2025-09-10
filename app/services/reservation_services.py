"""Service layer functions for reservation data operations"""

from bson import ObjectId

from app.extensions import mongo


def count_reservations_for_book(book_id: ObjectId) -> int:
    """Counts the total number of reservations for a given book ID"""
    return mongo.db.reservations.count_documents({"book_id": book_id})


def fetch_reservations_for_book(
    book_id: ObjectId, offset: int = 0, limit: int = 20
) -> list:
    """
    Fetches a paginated list of reservations for a book using an efficient
    aggregation pipeline to include user details.
    """
    pipeline = [
        # Stage 1: Find all reservations that match the book_id
        {"$match": {"book_id": book_id}},
        # Stage 2: Join ($lookup = JOIN in SQL) with the user collections
        {
            "$lookup": {
                "from": "users",  # The collection to join with
                "localField": "user_id",  # The field from the reservations collection
                "foreignField": "_id",  # The field from the users collection
                "as": "userDetails",  # The name of the new array field to add
            }
        },
        # Stage 3: $lookup returns an array. We only expect one user per reservation,
        # so $unwind flattens the array.
        {"$unwind": "$userDetails"},
        # Stage 4 & 5: Apply pagination to the result of the aggregation
        {"$skip": offset},
        {"$limit": limit},
    ]
    # use the aggregate() MongoDB collection method with 'pipeline'
    # tells MongoDb "run this aggregation pipeline against the collection"
    cursor = mongo.db.reservations.aggregate(pipeline)
    return list(cursor)
