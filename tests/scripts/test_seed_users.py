""" Test file for seeing database with user data"""
import pytest
import bcrypt
from app.extensions import mongo


def test_seed_users_successfully(test_app):
    """
    GIVEN an empty database and a list of user data
    WHEN the seed_users fucntion is called
    THEN the users should be created in the database with hashed passwords.
    """
    # Arrrange
    # define the user data we want to seed the database with
    sample_users = [
        {"email": "test.admin@example.com", "password": "AdminPassword123"},
        {"email": "test.user@example.com", "password": "UserPassword456"},
    ]

    # Ensure the database is clean beofre the test
    with test_app.app_context():
        mongo.db.users.delete_many({})

    # Act: call the function we are testing
    result_message = seed_users(sample_users)

    # Assert
    assert "Successfully seeded 2 users" in result_message
    # Check the database state directly
    with test_app.app_context():
        assert mongo.db.user.count_documents({}) == 2
        admin_user = mongo.db.users.find_one({"email": "test.admin@example.com"})
        assert admin_user is not None

        # Verify the password was hashed
        assert admin_user["password_hash"] != "AdminPassword123"
        assert bcrypt.checkpw(
            b"AdminPassword123",
            admin_user["password_hash"].encode("utf-8")
        )
