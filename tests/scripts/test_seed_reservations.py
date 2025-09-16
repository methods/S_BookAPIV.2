# pylint: disable=line-too-long
"""..."""

import json
from unittest.mock import MagicMock, mock_open, patch

import pytest
from bson import ObjectId
from pymongo.errors import PyMongoError

from app.datastore.mongo_db import (get_book_collection,
                                    get_reservation_collection,
                                    get_users_collection)
from app.extensions import mongo
from scripts import seed_reservations as load_reservations_module



def test_load_reservations_json_success():
    """
    GIVEN a valid JSON string representing reservation data
    WHEN load_reservations_json is called with a mock of the file system
    THEN it should return the parsed data as a list of dictionaries.
    """
    # Arrange
    test_reservations_data = """[
        {
        "book_title": "To Kill a Mockingbird",
        "user_identifier": "user_harper_l",
        "state": "reserved"
    },
    {
        "book_title": "Pride and Prejudice",
        "user_identifier": "user_jane_a",
        "state": "cancelled"
    }
    ]"""

    # use mock_open to simulate reading this valid content
    mocked_file = mock_open(read_data=test_reservations_data)

    with patch("builtins.open", mocked_file):

        # Act
        reservations = load_reservations_module.load_reservations_json()
        # Assert
        assert isinstance(reservations, list)
        assert len(reservations) == 2

        assert reservations[0]["book_title"] == "To Kill a Mockingbird"
        assert reservations[0]["user_identifier"] == "user_harper_l"
        assert reservations[0]["state"] == "reserved"
        assert reservations[-1]["book_title"] == "Pride and Prejudice"
        assert reservations[-1]["user_identifier"] == "user_jane_a"
        assert reservations[-1]["state"] == "cancelled"


def test_load_reservation_file_not_found(capsys):
    """
    GIVEN that the reservation data file is not found on the file system
    WHEN load_reservations_json is called
    THEN the function should return None and print a 'file not found' error message to stderr.
    """
    with patch("builtins.open", side_effect=FileNotFoundError()):
        result = load_reservations_module.load_reservations_json()

        assert result is None
        captured = capsys.readouterr()
        assert "ERROR: Data file not found" in captured.err


def test_load_reservations_json_decode_error(capsys):
    """
    GIVEN that the reservation data file contains invalid (malformed) JSON
    WHEN load_reservations_json is called
    THEN the function should handle the JSONDecodeError,
    return None, and print a helpful error message to stderr.
    """
    bad_json = '{"broken": }'  # invalid JSON
    m = mock_open(read_data=bad_json)
    # patch builtins.open so json.load() raises JSONDecodeError inside function
    with patch("builtins.open", m):
        result = load_reservations_module.load_reservations_json()

    assert result is None
    captured = capsys.readouterr()
    assert "Could not decode JSON" in captured.err


def test_load_reservations_integration_reads_file(tmp_path, monkeypatch):
    """
    Integration: create a temporary scripts/test_data/sample_reservations.json
    and monkeypatch module __file__ so load_reservations_json resolves to that path.
    """
    # Prepare temporary dir structure
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    test_data_dir = scripts_dir / "test_data"
    test_data_dir.mkdir()
    # IMPORTANT: create the exact filename the function expects
    file_path = test_data_dir / "sample_reservations.json"

    sample_data = [{"reservation_id": "r1", "status": "active"}]
    file_path.write_text(json.dumps(sample_data), encoding="utf-8")

    # Monkeypatch the module's __file__ so os.path.dirname(__file__) -> scripts_dir
    fake_module_file = scripts_dir / "seed_reservations.py"
    monkeypatch.setattr(load_reservations_module, "__file__", str(fake_module_file))

    # Call the function — it should read the created file
    result = load_reservations_module.load_reservations_json()
    assert result == sample_data


# -------------- TESTS for run_reservation_population -----------------

# A list of test cases for the failure scenarios
error_scenarios = [
    # id is a descriptive name that will appear in the test results
    pytest.param(None, [{"user_id": 1}], id="book_collection_is_empty"),
    pytest.param([{"id": 1}], None, id="reservation_collection_is_none"),
    pytest.param(None, None, id="both_collections_are_none"),
]


@pytest.mark.parametrize(
    "mock_books_return_val, mock_reservations_return_val", error_scenarios
)
@patch("scripts.seed_reservations.get_book_collection")
@patch("scripts.seed_reservations.get_reservation_collection")
def test_returns_404_if_any_collection_is_missing(
    mock_get_books,
    mock_get_reservations,  # Mocks come first
    test_app,  # fixture from conftest.py
    mock_books_return_val,
    mock_reservations_return_val,  # Params come after
):
    """
    GIVEN that either the book or reservation collection is missing (falsy)
    WHEN run_reservations_population is called
    THEN it should return a 404 error with a specific message
    """
    # ARRANGE: Use the parameters to set the return values of our mocks
    mock_get_books.return_value = mock_books_return_val
    mock_get_reservations.return_value = mock_reservations_return_val

    # ACT
    with test_app.app_context():
        response, status_code = load_reservations_module.run_reservation_population()

    # ASSERT: The expected outcome is the same for all parametrized cases
    assert status_code == 404
    assert response.get_json() == {"error": "Required collections could not be loaded."}

    # You can also assert that the first function was always called
    mock_get_books.assert_called_once()


# NOT A TRUE INTEGRATION TEST - NEED TO UPDATE
# def test_returns_200_when_collections_are_present(
#     test_app, mongo_setup, sample_book_data
# ):
#     """
#     GIVEN a database with books and reservations
#     WHEN run_reservations_population is called
#     THEN it should return a 200 success response
#     """
#     _ = mongo_setup

#     with test_app.app_context():

#         mock_books_collection_with_data = mongo.db.books
#         mock_reservations_collection_with_data = mongo.db.reservations

#         # SEED the collection directly with your sample data.
#         mock_books_collection_with_data.insert_many(sample_book_data)
#         mock_reservations_collection_with_data.insert_many(
#             [{"user_id": "user_george_o", "book_title": "A Book", "state": "reserved"}]
#         )

#         # 4. NOW, patch the helper functions to return THESE specific, seeded collection objects.
#         with patch(
#             "scripts.seed_reservations.get_book_collection",
#             return_value=mock_books_collection_with_data,
#         ), patch(
#             "scripts.seed_reservations.get_reservation_collection",
#             return_value=mock_reservations_collection_with_data,
#         ):

#             # ACT: Call the function. It will now use the seeded mongomock collection.
#             with test_app.app_context():
#                 success, message = run_reservation_population()

#     # ASSERT
#     assert success is True
#     assert message == "Successfully created 10 and updated 0 reservations."


def test_run_population_logic_with_controlled_inputs(test_app, mongo_setup):
    """
    GIVEN a database with two specific books
    AND a known, small list of reservation data is provided
    WHEN run_reservation_population is called
    THEN it correctly processes only the matching reservations.
    """
    _ = mongo_setup

    # 1. Arrange: Control ALL external inputs
    # Input #1: The books in the database
    books_in_db = [
        {"_id": ObjectId(), "title": "1984"},
        {"_id": ObjectId(), "title": "Dune"},
    ]

    # Input #2: The users in the db
    users_in_db = [
        {"_id": ObjectId(), "email": "test_user1@example.com"},
        {"_id": ObjectId(), "email": "test_user2@example.com"},
    ]
    # Input #3: The data we PRETEND comes from the JSON file
    reservations_to_load = [
        {
            "book_title": "1984",
            "user_email": "test_user1@example.com",
            "state": "reserved",
            "surname": "a",
            "forenames": "b",
        },
        {
            "book_title": "Dune",
            "user_email": "test_user2@example.com",
            "state": "pending",
            "surname": "c",
            "forenames": "d",
        },
        {
            "book_title": "Unrelated Book",
            "user_email": "test_user3@example.com",
            "state": "reserved",
            "surname": "e",
            "forenames": "f",
        },
    ]

    with test_app.app_context():
        # Setup the fake database
        mongo.db.books.insert_many(books_in_db)
        mongo.db.users.insert_many(users_in_db)

        # 2. Patch ALL dependencies to return our controlled inputs
        with patch(
            "scripts.seed_reservations.get_book_collection", return_value=mongo.db.books
        ), patch(
            "scripts.seed_reservations.get_reservation_collection",
            return_value=mongo.db.reservations,
        ), patch(
            "scripts.seed_reservations.get_users_collection",
            return_value=mongo.db.users,
        ), patch(
            "scripts.seed_reservations.load_reservations_json",
            return_value=reservations_to_load,
        ):

            # 3. Act: Run the function under test
            success, message = load_reservations_module.run_reservation_population()

    # 4. Assert: Check against a predictable, stable result
    assert success is True
    # The result is now independent of the large JSON file. We expect 2 creations.
    assert message == "Successfully created 2 and updated 0 reservations."


def test_returns_warning_when_no_books_are_found(test_app):
    """
    GIVEN get_book_collection returns a collection that finds no books
    WHEN run_reservation_population is called
    THEN it should return a tuple with a warning message
    """
    # ARRANGE
    # 1. Create a mock collection object. This simulates the real collection.
    mock_books_collection = MagicMock()

    # 2. Control what `.find()` returns:
    # make it return an empty list to simulate no books being found.
    mock_books_collection.find.return_value = []

    with patch(
        "scripts.seed_reservations.get_book_collection",
        return_value=mock_books_collection,
    ), patch(
        "scripts.seed_reservations.get_reservation_collection", return_value=MagicMock()
    ):
        # ACT
        with test_app.app_context():
            # In Flask, non-jsonify responses don't get split into (response, status)
            # So we just capture the single return value.
            result = load_reservations_module.run_reservation_population()

    # ASSERT
    expected_warning = (
        True,
        "Warning: No books found in the database. Cannot create reservations.",
    )
    assert result == expected_warning

    mock_books_collection.find.assert_called_once_with({}, {"_id": 1, "title": 1})


def test_returns_error_on_pymongo_error(test_app):
    """
    GIVEN the database call to find books raises a PyMongoError
    WHEN run_reservation_population is called
    THEN it should catch the exception and return a tuple with an error message
    """
    # ARRANGE
    mock_books_collection = MagicMock()

    # 2. Control the BEHAVIOR of .find() with .side_effect
    error_message = "Database connection failed"
    mock_books_collection.find.side_effect = PyMongoError(error_message)

    # 3. Patch the helpers
    with patch(
        "scripts.seed_reservations.get_book_collection",
        return_value=mock_books_collection,
    ), patch(
        "scripts.seed_reservations.get_users_collection", return_value=MagicMock()
    ), patch(
        "scripts.seed_reservations.get_reservation_collection", return_value=MagicMock()
    ):

        # ACT
        with test_app.app_context():
            result = load_reservations_module.run_reservation_population()

    # ASSERT
    assert result == (
        False,
        "ERROR: Failed to fetch data from database: Database connection failed",
    )


def test_creates_book_id_map_and_proceeds_on_happy_path(test_app):
    """
    GIVEN the database contains books
    WHEN run_reservation_population is called
    THEN it should create the book_id_map, users_id_map and proceed successfully
    """
    # ARRANGE
    mock_books_collection = MagicMock()
    mock_users_collection = MagicMock()

    # Simulate a successful find() call that returns documents
    sample_books_cursor = [
        {"_id": ObjectId(), "title": "To Kill a Mockingbird"},
        {"_id": ObjectId(), "title": "1984"},
    ]
    mock_books_collection.find.return_value = sample_books_cursor

    # Input #2: The users in the db
    sample_users_data = [
        {"_id": ObjectId(), "email": "test_user1@example.com"},
        {"_id": ObjectId(), "email": "test_user2@example.com"},
    ]
    mock_users_collection.find.return_value = sample_users_data

    # Also mock the file read to return a small, predictable list
    mock_reservation_data = [
        {
            "book_title": "1984",
            "user_email": "test_user1@example.com",
            "state": "reserved",
            "surname": "a",
            "forenames": "b",
        }
    ]

    # 3. Patch ALL external dependencies
    # Patch ALL external dependencies
    with patch(
        "scripts.seed_reservations.get_book_collection",
        return_value=mock_books_collection,
    ), patch(
        "scripts.seed_reservations.get_reservation_collection", return_value=MagicMock()
    ), patch(
        "scripts.seed_reservations.get_users_collection",
        return_value=mock_users_collection,
    ), patch(
        "scripts.seed_reservations.load_reservations_json",
        return_value=mock_reservation_data,
    ):

        # ACT
        with test_app.app_context():
            success, message = load_reservations_module.run_reservation_population()

    # ASSERT
    # Check that we made it to the end of the function successfully
    assert success is True
    assert message == "Successfully created 1 and updated 0 reservations."

    # Crucially, verify that the database was queried correctly
    mock_books_collection.find.assert_called_once_with({}, {"_id": 1, "title": 1})


def test_returns_error_if_reservation_json_fails_to_load(test_app, mongo_setup):
    """
    GIVEN the JSON file cannot be loaded
    WHEN run_reservation_population is called
    THEN it should return a failure tuple and not attempt to process reservations.
    """
    # ARRANGE
    _ = mongo_setup

    # 1. Seed the database with the prerequisites (books and users)
    #    so the function can get past the initial checks.
    with test_app.app_context():
        # Use the helpers to get the collections your app is configured to use
        books = get_book_collection()
        users = get_users_collection()

        books.insert_one({"_id": ObjectId(), "title": "A Book"})
        users.insert_one({"_id": ObjectId(), "email": "a@b.com"})

    # 2. Patch the one dependency we want to fail: `load_reservations_json`.
    #    Use patch.object for better robustness in CI environments.
        with patch.object(load_reservations_module, "load_reservations_json", return_value=None) as mock_load_json:
            # ACT
            with test_app.app_context():
                success, message = load_reservations_module.run_reservation_population()

    # ASSERT
    # 3. Check that the function correctly reported the failure.
    assert success is False
    assert message == "Failed to load reservation data."
    # 4. Verify that the function did attempt to load the JSON.
    mock_load_json.assert_called_once()



def test_proceeds_when_reservation_json_loads_successfully(test_app):
    """
    GIVEN a database with a book and a user
    AND the JSON file provides one matching reservation
    WHEN run_reservation_population is called
    THEN it should successfully create one new reservation in the database.
    """
    # This test manages its own setup and teardown to have full control over the timing.
    try:
        # ARRANGE
        # 1. Seed the database with prerequisites inside an app context.
        with test_app.app_context():
            books = get_book_collection()
            users = get_users_collection()
            reservations_collection = get_reservation_collection()

            # Start with a clean slate for this specific test
            books.delete_many({})
            users.delete_many({})
            reservations_collection.delete_many({})

            book_id = books.insert_one({"title": "A Book"}).inserted_id
            user_id = users.insert_one({"email": "test@example.com"}).inserted_id

        # 2. Define the fake data that our patched function will return.
        sample_reservation_data = [
            {
                "user_email": "test@example.com",
                "book_title": "A Book",
                "state": "reserved",
                "surname": "User",
                "forenames": "Test",
            }
        ]

        # 3. Patch the file I/O dependency.
        with patch(
            "scripts.seed_reservations.load_reservations_json",
            return_value=sample_reservation_data,
        ):
            # ACT
            with test_app.app_context():
                success, _message = load_reservations_module.run_reservation_population()

        # ASSERT
        # 4. Check that the function reported success.
        assert success is True

        # 5. The most important check: Verify the final state of the database.
        with test_app.app_context():
            reservations_collection = get_reservation_collection()
            assert reservations_collection.count_documents({}) == 1
            created_reservation = reservations_collection.find_one()

            assert created_reservation is not None
            assert created_reservation["book_id"] == book_id
            assert created_reservation["user_id"] == user_id
            assert created_reservation["state"] == "reserved"

    finally:
        # TEARDOWN: This block is guaranteed to run, even if the assertions fail.
        with test_app.app_context():
            get_book_collection().delete_many({})
            get_users_collection().delete_many({})
            get_reservation_collection().delete_many({})


def test_skips_reservation_if_book_title_not_found(test_app, capsys):
    """
    GIVEN a database with a book and user, but the provided reservation data has an unknown book title
    WHEN run_reservation_population is called
    THEN it should print a warning, create no reservations, and complete successfully.
    """
    # This test manages its own setup and teardown to be self-contained.
    try:
        # ARRANGE
        # 1. Seed the DB using the helpers to write to the correct collections.
        with test_app.app_context():
            books = get_book_collection()
            users = get_users_collection()
            reservations = get_reservation_collection()

            # Start with a clean slate
            books.delete_many({})
            users.delete_many({})
            reservations.delete_many({})

            books.insert_one({"title": "The Hobbit"})
            users.insert_one({"email": "test@example.com"})

        # 2. Create reservation data that references a book title that does NOT exist.
        reservation_with_bad_title = [
            {
                "book_title": "A Book That Does Not Exist",
                "user_email": "test@example.com",
                "state": "reserved",
                "surname": "User",
                "forenames": "Test",
            }
        ]

        # 3. Patch the file I/O dependency.
        with patch(
            "scripts.seed_reservations.load_reservations_json",
            return_value=reservation_with_bad_title,
        ):
            # ACT
            with test_app.app_context():
                success, _message = load_reservations_module.run_reservation_population()

        # ASSERT
        assert success is True

        # Check that the correct warning was printed.
        captured = capsys.readouterr()
        assert "WARNING: Skipping reservation" in captured.out
        assert "'A Book That Does Not Exist'" in captured.out

        # Verify that no reservations were actually created.
        with test_app.app_context():
            assert get_reservation_collection().count_documents({}) == 0

    finally:
        # TEARDOWN: Ensure everything is clean for the next test.
        with test_app.app_context():
            get_book_collection().delete_many({})
            get_users_collection().delete_many({})
            get_reservation_collection().delete_many({})


def test_proceeds_if_book_title_is_found(test_app, capsys):
    """
    GIVEN a reservation's book_title IS in the book_id_map
    WHEN run_reservation_population is called
    THEN it should not print a warning and should proceed
    """
    # ARRANGE
    # 1. The book map has a specific, known book.
    mock_books_collection = MagicMock()
    book_title_to_find = "The Lord of the Rings"
    sample_book_for_map = [{"_id": ObjectId(), "title": book_title_to_find}]
    mock_books_collection.find.return_value = sample_book_for_map

    # 2. The reservation data refers to that EXACT book title.
    reservation_with_good_title = [
        {
            "book_title": book_title_to_find,
            "user_id": "another_user_456",
            "state": "pending",
            "surname": "test1",
            "forenames": "test1fore",
        }
    ]

    # 3. Patch dependencies.
    with patch(
        "scripts.seed_reservations.get_book_collection",
        return_value=mock_books_collection,
    ), patch(
        "scripts.seed_reservations.get_reservation_collection", return_value=MagicMock()
    ), patch(
        "scripts.seed_reservations.load_reservations_json",
        return_value=reservation_with_good_title,
    ):

        # ACT
        with test_app.app_context():
            success, _message = load_reservations_module.run_reservation_population()

    # ASSERT
    assert success is True

    # Crucially, assert that NO warning was printed.
    captured = capsys.readouterr()
    warning_message_to_avoid = "WARNING: Skipping reservation"
    assert warning_message_to_avoid not in captured.out


def test_creates_new_reservation_if_not_exists(test_app):
    """
    GIVEN a reservation does not exist in the database
    WHEN run_reservation_population processes it
    THEN it should call update_one with upsert=True and increment created_count.
    """
    # ARRANGE
    # 1. Define the data we will use in our mocks.
    mock_book_id = ObjectId()
    mock_user_id = ObjectId()
    user_email = "test@example.com"
    book_title = "The Hobbit"

    # 2. Mock the book collection to return our book.
    mock_books_collection = MagicMock()
    mock_books_collection.find.return_value = [
        {"_id": mock_book_id, "title": book_title}
    ]

    # 3. Mock the user collection to return our user.
    mock_users_collection = MagicMock()
    mock_users_collection.find.return_value = [
        {"_id": mock_user_id, "email": user_email}
    ]

    # 4. Define the data coming from the JSON file.
    reservations_from_json = [
        {
            "user_email": user_email,
            "book_title": book_title,
            "state": "reserved",
            "surname": "test1",
            "forenames": "test1fore",
        }
    ]

    # 5. Mock the reservations collection and the result of its update_one call.
    mock_reservations_collection = MagicMock()
    mock_upsert_result = MagicMock()
    mock_upsert_result.upserted_id = ObjectId()  # A non-None value signals a creation
    mock_upsert_result.matched_count = 0
    mock_reservations_collection.update_one.return_value = mock_upsert_result

    # 6. Patch all dependencies.
    with patch(
        "scripts.seed_reservations.get_book_collection",
        return_value=mock_books_collection,
    ), patch(
        "scripts.seed_reservations.get_reservation_collection",
        return_value=mock_reservations_collection,
    ), patch(
        "scripts.seed_reservations.get_users_collection",
        return_value=mock_users_collection,
    ), patch(
        "scripts.seed_reservations.load_reservations_json",
        return_value=reservations_from_json,
    ):

        # ACT
        with test_app.app_context():
            success, message = load_reservations_module.run_reservation_population()

    # ASSERT
    assert success is True

    # Assert that the database method was called with the correct ObjectIds
    expected_filter = {"user_id": mock_user_id, "book_id": mock_book_id}
    expected_update = {
        "$set": {
            "user_id": mock_user_id,
            "book_id": mock_book_id,
            "state": "reserved",
            "surname": "test1",
            "forenames": "test1fore",
        }
    }
    mock_reservations_collection.update_one.assert_called_once_with(
        expected_filter, expected_update, upsert=True
    )

    # Assert the final counts in the success message
    expected_message = "Successfully created 1 and updated 0 reservations."
    assert message == expected_message


def test_updates_existing_reservation_if_found(test_app):
    """
    GIVEN a reservation already exists in the database
    WHEN run_reservation_population processes it
    THEN it should call update_one and increment updated_count.
    """
    # ARRANGE
    # 1. Define the data we will use in our mocks.
    mock_book_id = ObjectId()
    mock_user_id = ObjectId()
    user_email = "test.update@example.com"
    book_title = "1984"

    # 2. Mock the book collection to return our book.
    mock_books_collection = MagicMock()
    mock_books_collection.find.return_value = [
        {"_id": mock_book_id, "title": book_title}
    ]

    # 3. NEW: Mock the user collection to return our user.
    mock_users_collection = MagicMock()
    mock_users_collection.find.return_value = [
        {"_id": mock_user_id, "email": user_email}
    ]

    # 4. Define the data from the JSON file, which will update an existing record.
    reservations_from_json = [
        {
            "user_email": user_email,
            "book_title": book_title,
            "state": "returned",  # The new state to be updated
            "surname": "Updated",
            "forenames": "User",
        }
    ]

    # 5. Mock the reservations collection and the result of a successful UPDATE.
    mock_reservations_collection = MagicMock()
    mock_update_result = MagicMock()
    mock_update_result.upserted_id = None  # None signals it was NOT a creation
    mock_update_result.matched_count = 1  # 1 signals it found and updated a document
    mock_reservations_collection.update_one.return_value = mock_update_result

    # 6. Patch all dependencies, including the new get_users_collection.
    with patch(
        "scripts.seed_reservations.get_book_collection",
        return_value=mock_books_collection,
    ), patch(
        "scripts.seed_reservations.get_reservation_collection",
        return_value=mock_reservations_collection,
    ), patch(
        "scripts.seed_reservations.get_users_collection",
        return_value=mock_users_collection,
    ), patch(
        "scripts.seed_reservations.load_reservations_json",
        return_value=reservations_from_json,
    ):

        # ACT
        with test_app.app_context():
            success, message = load_reservations_module.run_reservation_population()

    # ASSERT
    assert success is True
    mock_reservations_collection.update_one.assert_called_once()

    # Assert the final counts in the success message
    expected_message = "Successfully created 0 and updated 1 reservations."
    assert message == expected_message


def test_returns_error_on_reservation_upsert_failure(test_app):
    """
    GIVEN the call to update_one raises a PyMongoError
    WHEN run_reservation_population processes a reservation
    THEN it should catch the error and return a failure tuple.
    """
    # ARRANGE
    # 1. Define the data we will use in our mocks.
    mock_book_id = ObjectId()
    mock_user_id = ObjectId()
    user_email = "test.error@example.com"
    book_title = "Dune"

    # 2. Mock the book collection to return our book.
    mock_books_collection = MagicMock()
    mock_books_collection.find.return_value = [
        {"_id": mock_book_id, "title": book_title}
    ]

    # 3. NEW: Mock the user collection to return our user.
    mock_users_collection = MagicMock()
    mock_users_collection.find.return_value = [
        {"_id": mock_user_id, "email": user_email}
    ]

    # 4. Define the data coming from the JSON file.
    reservations_from_json = [
        {
            "user_email": user_email,
            "book_title": book_title,
            "state": "reserved",
            "surname": "test1",
            "forenames": "test1fore",
        }
    ]

    # 5. Mock the reservations collection and configure update_one to RAISE an error.
    mock_reservations_collection = MagicMock()
    error_message = "Connection refused"
    mock_reservations_collection.update_one.side_effect = PyMongoError(error_message)

    # 6. Patch all dependencies.
    with patch(
        "scripts.seed_reservations.get_book_collection",
        return_value=mock_books_collection,
    ), patch(
        "scripts.seed_reservations.get_reservation_collection",
        return_value=mock_reservations_collection,
    ), patch(
        "scripts.seed_reservations.get_users_collection",
        return_value=mock_users_collection,
    ), patch(
        "scripts.seed_reservations.load_reservations_json",
        return_value=reservations_from_json,
    ):

        # ACT
        with test_app.app_context():
            success, message = load_reservations_module.run_reservation_population()

    # ASSERT
    assert success is False
    expected_error_message = (
        f"ERROR: Failed to upsert reservation for user '{user_email}': {error_message}"
    )
    assert message == expected_error_message
