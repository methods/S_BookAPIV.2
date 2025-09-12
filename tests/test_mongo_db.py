"""Test file for utility/helper functions that interact with MongoDb"""

import pytest
from pymongo.collection import Collection

from app import create_app
from app.datastore.mongo_db import (get_reservation_collection,
                                    get_users_collection)
from app.extensions import mongo


@pytest.fixture(scope="module")
def integration_app():
    """
    Creates a new Flask application for a test module.
    Configured for testing, including a separate test database.
    """
    integration_test_app = create_app(
        {"TESTING": True, "MONGO_URI": "mongodb://localhost:27017/my_library_db_test"}
    )

    with integration_test_app.app_context():
        yield integration_test_app

    # Teardown
    print("\nDropping test database...")
    mongo.cx.drop_database("my_library_db_test")


def test_get_reservation_collection_integration(
    integration_app,
):  # pylint: disable=redefined-outer-name
    """
    GIVEN a Flask application configured for testing
    WHEN the get_reservation_collection() helper is called within an app context,
    THEN it should return a valid PyMongo Collection object for the 'reservations collection'
    """
    with integration_app.app_context():
        # Act
        reservations_collection = get_reservation_collection()

        # Assert
        assert isinstance(reservations_collection, Collection)
        assert reservations_collection.name == "reservations"

        # Proving the connection works
        try:
            test_doc = {"_id": "test_reservations", "status": "active"}
            reservations_collection.insert_one(test_doc)

            retrieved_doc = mongo.db.reservations.find_one({"_id": "test_reservations"})
            print("retrieved_doc", retrieved_doc)
            assert retrieved_doc is not None
            assert retrieved_doc["status"] == "active"
        finally:
            # Cleanup- ALWAYS clean up what you create within a single test
            reservations_collection.delete_many({})


def test_get_users_collection_integration(
    integration_app,
):  # pylint: disable=redefined-outer-name
    """
    GIVEN a Flask application configured for testing
    WHEN the get_users_collection() helper is called within an app context,
    THEN it should return a valid PyMongo Collection object for the 'reservations collection'
    """
    with integration_app.app_context():
        # Act
        users_collection = get_users_collection()

        # Assert
        assert isinstance(users_collection, Collection)
        assert users_collection.name == "users"

        # Proving the connection works
        try:
            test_doc = {"_id": "test_user", "role": "user"}
            users_collection.insert_one(test_doc)

            retrieved_doc = mongo.db.users.find_one({"_id": "test_user"})
            print("retrieved_doc", retrieved_doc)
            assert retrieved_doc is not None
            assert retrieved_doc["role"] == "user"
        finally:
            # Cleanup- ALWAYS clean up what you create within a single test
            users_collection.delete_many({})
