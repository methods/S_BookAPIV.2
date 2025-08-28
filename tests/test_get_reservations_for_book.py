"""..."""
import datetime
from bson import ObjectId
import pytest
import jwt


# A valid ObjectId for a book that we'll pretend exists in the DB
EXISTING_BOOK_ID = "6154a1d34e6f1c2b3a4d5e6f"
# A valid ObjectId for a book that has no reservations
NO_RESERVATIONS_BOOK_ID = "6154a1d34e6f1c2b3a4d5e70"
# A valid ObjectId for a book that does not exist
NON_EXISTENT_BOOK_ID = "000000000000000000000000"
# An invalid ObjectId string
INVALID_BOOK_ID = "this-is-not-an-object-id"


def create_auth_token(user_id, role, secret_key):
    """
    HELPER function to create tokens for testing.
    """
    payload = {
        "user_id": str(user_id),
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    }

    return jwt.encode(payload, secret_key, algorithm="HS256")

# -------- TESTS ---------