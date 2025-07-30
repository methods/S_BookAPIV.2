# pylint: disable=missing-docstring

from unittest.mock import ANY, MagicMock, patch

import pytest
from bson.objectid import ObjectId
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app import create_app, routes
from app.datastore.mongo_db import get_book_collection

# Mock book database object
books_database = [
    {
        "id": "1",
        "title": "The Great Adventure",
        "synopsis": "A thrilling adventure through the jungles of South America.",
        "author": "Jane Doe",
        "links": {
            "self": "/books/1",
            "reservations": "/books/1/reservations",
            "reviews": "/books/1/reviews",
        },
        "state": "active",
    },
    {
        "id": "2",
        "title": "Mystery of the Old Manor",
        "synopsis": "A detective story set in an old manor with many secrets.",
        "author": "John Smith",
        "links": {
            "self": "/books/2",
            "reservations": "/books/2/reservations",
            "reviews": "/books/2/reviews",
        },
        "state": "active",
    },
    {
        "id": "3",
        "title": "The Science of Everything",
        "synopsis": "An in-depth look at the scientific principles that govern our world.",
        "author": "Alice Johnson",
        "links": {
            "self": "/books/3",
            "reservations": "/books/3/reservations",
            "reviews": "/books/3/reviews",
        },
        "state": "deleted",
    },
]

# ------------------- Tests for POST ---------------------------------------------


def test_add_book_creates_and_returns_new_book(client, _insert_book_to_db, monkeypatch):

    test_book = {
        "title": "Test Book",
        "author": "AN Other",
        "synopsis": "Test Synopsis",
    }

    # Mock the 'replace_one' operation
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = ObjectId()

    # Mock the full book document that 'find_one' will return
    mock_book_from_db = test_book.copy()
    mock_book_from_db["_id"] = mock_insert_result.inserted_id
    mock_book_from_db["links"] = {"self": f"/books/{mock_insert_result.inserted_id}"}

    # Mock the entire db collection object and its methods
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = mock_book_from_db

    # Create a mock for the helper function that returns our mock result
    mock_insert_helper = MagicMock(return_value=mock_insert_result)

    # Apply all the patches
    monkeypatch.setattr("app.routes.get_book_collection", lambda: mock_collection)
    monkeypatch.setattr("app.routes.insert_book_to_mongo", mock_insert_helper)
    monkeypatch.setattr("app.routes.append_hostname", lambda book, host: book)

    # Define the valid headers, including the API key that matches conftest.py
    valid_headers = {"X-API-KEY": "test-key-123"}

    # Act
    response = client.post("/books", json=test_book, headers=valid_headers)

    # Assert
    assert response.status_code == 201

    # Now these assertions will work correctly!
    mock_insert_helper.assert_called_once_with(test_book, mock_collection)
    mock_collection.update_one.assert_called_once()
    mock_collection.find_one.assert_called_once()

    # Assert the response body is correct
    response_data = response.get_json()
    assert response_data["id"] == str(mock_insert_result.inserted_id)
    assert response_data["title"] == test_book["title"]
    assert "_id" not in response_data


def test_add_book_sent_with_missing_required_fields(client):
    test_book = {
        "author": "AN Other"
        # missing 'title' and 'synopsis'
    }

    # Define the valid headers, including the API key that matches conftest.py
    valid_headers = {"X-API-KEY": "test-key-123"}
    response = client.post("/books", json=test_book, headers=valid_headers)

    assert response.status_code == 400
    response_data = response.get_json()
    assert "error" in response_data
    assert "Missing required fields: title, synopsis" in response.get_json()["error"]


def test_add_book_sent_with_wrong_types(client):
    test_book = {"title": 1234567, "author": "AN Other", "synopsis": "Test Synopsis"}

    # Define the valid headers, including the API key that matches conftest.py
    valid_headers = {"X-API-KEY": "test-key-123"}
    response = client.post("/books", json=test_book, headers=valid_headers)

    assert response.status_code == 400
    response_data = response.get_json()
    assert "error" in response_data
    assert "Field title is not of type <class 'str'>" in response.get_json()["error"]


def test_add_book_with_invalid_json_content(client):

    # Define the valid headers, including the API key that matches conftest.py
    valid_headers = {"X-API-KEY": "test-key-123"}

    # This should trigger a TypeError
    response = client.post(
        "/books", json="This is not a JSON object", headers=valid_headers
    )

    assert response.status_code == 400
    assert "JSON payload must be a dictionary" in response.get_json()["error"]


def test_add_book_check_request_header_is_json(client):
    # Define the valid headers, including the API key that matches conftest.py
    valid_headers = {"X-API-KEY": "test-key-123"}

    response = client.post(
        "/books",
        data="This is not a JSON object",
        headers={"content-type": "text/plain", **valid_headers},
    )

    assert response.status_code == 415
    assert "Request must be JSON" in response.get_json()["error"]


def test_500_response_is_json(client):
    # Arrange
    test_book = {
        "title": "Valid Title",
        "author": "AN Other",
        "synopsis": "Test Synopsis",
    }

    valid_headers = {"X-API-KEY": "test-key-123"}

    error_message = "An unexpected error occurred"

    # Use patch to mock uuid module failing and throwing an exception
    with patch("app.routes.insert_book_to_mongo", side_effect=Exception(error_message)):
        response = client.post("/books", json=test_book, headers=valid_headers)

        # ASSERT
        assert response.status_code == 500
        assert response.content_type == "application/json"

        assert "An unexpected error occurred" in response.get_json()["error"]


# ------------------------ Tests for GET --------------------------------------------


@patch("app.routes.format_books_for_api")
@patch("app.routes.fetch_active_books")
def test_get_all_books_returns_all_books(mock_fetch, mock_format, client):

    mock_books_list = MagicMock()
    mock_fetch.return_value = mock_books_list

    mock_formatted_data = [
        {"id": "1", "title": "A", "synopsis": "x", "author": "y", "links": {}},
        {"id": "2", "title": "B", "synopsis": "z", "author": "w", "links": {}},
    ]

    mock_format.return_value = (mock_formatted_data, None)

    response = client.get("/books")

    # Assert HTTP properties
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    # Assert the response body
    response_data = response.get_json()
    assert isinstance(response_data, dict)
    assert response_data["total_count"] == 2
    assert response_data["items"] == mock_formatted_data

    # Assert that mocks were called correctly
    mock_fetch.assert_called_once()
    mock_format.assert_called_once_with(mock_books_list, "http://localhost")


@patch("app.routes.fetch_active_books")
def test_missing_fields_in_book_object_returned_by_database(mock_fetch, client):

    bad_raw_data = [
        {"id": "1", "synopsis": "x", "author": "y", "links": {}},  # Missing 'title'
        {"id": "2", "title": "B", "author": "w", "links": {}},  # Missing 'synopsis'
    ]
    mock_fetch.return_value = bad_raw_data

    expected_error_message = (
        "Missing required fields:\n"
        f"- title in book: {bad_raw_data[0]}\n"
        f"- synopsis in book: {bad_raw_data[1]}"
    )

    # --- ACT ---
    response = client.get("/books")

    # --- ASSERT ---
    assert response.status_code == 500

    response_data = response.get_json()
    assert "error" in response_data
    assert response_data["error"] == expected_error_message
    mock_fetch.assert_called_once()


@patch("app.routes.fetch_active_books")
def test_get_all_books_returns_error_404_when_list_is_empty(mock_fetch, client):
    empty_data = []
    mock_fetch.return_value = empty_data
    response = client.get("/books")
    assert response.status_code == 404
    assert "No books found" in response.get_json()["error"]


@patch("app.routes.fetch_active_books")
def test_get_book_returns_404_when_books_is_none(mock_fetch, client):
    none_data = None
    mock_fetch.return_value = none_data
    response = client.get("/books")
    assert response.status_code == 404
    assert "No books found" in response.get_json()["error"]


@patch("app.services.book_service.find_books")
def test_get_books_retrieves_and_formats_books_correctly(mock_find_books, client):
    """
    GIVEN a mocked database service
    WHEN the /books endpoint is called
    THEN the service layer correctly queries the database for non-deleted books
    AND the API response is correctly formatted with absolute URLs
    """
    # ARRANGE
    filtered_db_result = [
        {
            "_id": "2",
            "title": "Mystery of the Old Manor",
            "author": "John Smith",
            "synopsis": "A detective story set in an old manor with many secrets.",
            "links": {
                "self": "/books/2",
                "reservations": "/books/2/reservations",
                "reviews": "/books/2/reviews",
            },
            "state": "active",
        },
        {
            "_id": "3",
            "title": "The Science of Everything",
            "author": "Alice Johnson",
            "synopsis": "An in-depth look at the scientific principles that govern our world.",
            "links": {
                "self": "/books/3",
                "reservations": "/books/3/reservations",
                "reviews": "/books/3/reviews",
            },
            # No 'state' field, correctly simulating a record that is implicitly active.
        },
    ]
    mock_find_books.return_value = filtered_db_result

    base_url = "http://localhost"
    expected_response_items = [
        {
            "id": "2",  # Renamed from _id
            "title": "Mystery of the Old Manor",
            "author": "John Smith",
            "synopsis": "A detective story set in an old manor with many secrets.",
            "links": {
                "self": f"{base_url}/books/2",
                "reservations": f"{base_url}/books/2/reservations",
                "reviews": f"{base_url}/books/2/reviews",
            },
        },
        {
            "id": "3",  # Renamed from _id
            "title": "The Science of Everything",
            "author": "Alice Johnson",
            "synopsis": "An in-depth look at the scientific principles that govern our world.",
            "links": {
                "self": f"{base_url}/books/3",
                "reservations": f"{base_url}/books/3/reservations",
                "reviews": f"{base_url}/books/3/reviews",
            },
        },
    ]

    # ACT
    response = client.get("/books")

    # ASSERT
    assert response.status_code == 200
    # 1) Service layer called with correct filter
    expected_db_filter = {"state": {"$ne": "deleted"}}
    mock_find_books.assert_called_once_with(ANY, query_filter=expected_db_filter)
    # 2) Response formatting is exactly as expected
    response_data = response.get_json()
    assert response_data["items"] == expected_response_items
    assert len(response_data["items"]) == 2


@patch("app.services.book_service.get_book_collection")
def test_get_books_handles_database_connection_error(mock_get_collection, client):
    """
    GIVEN the database connection fails
    WHEN the /books endpoint is called
    THEN a 503 Service Unavailable error should be returned with a friendly message.
    """
    # ARRANGE: Configure the mock to raise the exception when called
    mock_get_collection.side_effect = ConnectionFailure("Could not connect to DB")

    # ACT
    response = client.get("/books")

    # ASSERT
    assert response.status_code == 503  # Now asserting the correct code

    # This assertion will now pass because your controller is returning the correct message
    expected_error = "The database service is temporarily unavailable."
    assert expected_error in response.json["error"]["message"]


# -------- Tests for GET a single resource ----------------


def test_get_book_happy_path_unit_test(client, monkeypatch):
    # Arrange:
    fake_book_id = ObjectId()
    fake_book_id_str = str(fake_book_id)
    fake_book_from_db = {
        "_id": fake_book_id,
        "title": "A Mocked Book",
        "author": "The Mockist",
        "synopsis": "A tale of fakes and stubs.",
        "state": "active",
        "links": {},  # This will be populated by the append_hostname helper
    }

    # intercept the call to the service function
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = fake_book_from_db

    # use monkeypatch to replace the get_book_collection
    monkeypatch.setattr("app.routes.get_book_collection", lambda: mock_collection)

    # ACT
    get_response = client.get(f"/books/{fake_book_id_str}")

    # ASSERT
    assert get_response.status_code == 200
    response_data = get_response.get_json()
    assert response_data["title"] == "A Mocked Book"
    assert response_data["id"] == fake_book_id_str
    mock_collection.find_one.assert_called_once()
    mock_collection.find_one.assert_called_once_with(
        {"_id": fake_book_id, "state": {"$ne": "deleted"}}
    )  # pylint: disable=line-too-long


def test_get_book_returns_specified_book(
    client, db_setup
):  # pylint: disable=unused-argument
    """This is an INTEGRATION test"""
    # The 'db_setup' fixture has already cleaned the db
    # and provided the app.context

    with client.application.app_context():
        # GIVEN: Setup the db
        collection = get_book_collection()

        sample_book = {
            "_id": ObjectId(),  # Generate a new valid ObjectId
            "title": "Test Driven Development",
            "author": "Kent Beck",
            "synopsis": "A guide to TDD.",
            "state": "active",
            "links": {},  # can be empty for this test
        }
        collection.insert_one(sample_book)
        book_id_str = str(sample_book["_id"])

        # ACT
        get_response = client.get(f"/books/{book_id_str}")
        assert get_response.status_code == 200
        assert get_response.content_type == "application/json"
        response_data = get_response.get_json()
        assert response_data["id"] == book_id_str
        assert response_data["title"] == "Test Driven Development"
        assert response_data["author"] == "Kent Beck"


def test_get_book_with_invalid_id_format_returns_400(client, db_setup):  # pylint: disable=unused-argument
    # Arrange
    # an ID that is clearly not a valid MongoDB ObjectId
    invalid_book_id = "this-is-not-a-valid-id"

    # Act
    response = client.get(f"/books/{invalid_book_id}")

    # Assert
    assert response.status_code == 400
    assert response.content_type == "application/json"

    # Check that the JSON error message is exactly what the code returns
    expected_error = {"error": "Invalid book ID format"}
    assert response.get_json() == expected_error

def test_get_book_not_found_returns_404(client, monkeypatch):
    """
    WHEN given a well-formed but non-existent ObjectId,
    Returns a 404 error
    """
    # Arrange
    valid_but_missing_id = ObjectId()
    valid_id_str = str(valid_but_missing_id)

    # Mock the collection to return None (book not in DB)
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    monkeypatch.setattr(routes, "get_book_collection", lambda: mock_collection)

    # ACT: Test GET request using invalid book ID
    response = client.get(f"/books/{valid_id_str}")

    assert response.status_code == 404
    assert response.content_type == "application/json"
    assert "Book not found" in response.get_json()["error"]


def test_book_database_is_initialized_for_specific_book_route(client, monkeypatch):
    """
    WHEN get_book_collection() returns None
    THEN the /books/<id> route should return HTTP 500
    """
    # Arrange
    valid_id = ObjectId()
    valid_id_str = str(valid_id)

    monkeypatch.setattr(routes, "get_book_collection", lambda: None)

    response = client.get(f"/books/{valid_id_str}")
    assert response.status_code == 500
    assert "Book collection not found" in response.get_json()["error"]


def test_get_book_returns_404_if_state_equals_deleted(client, monkeypatch):
    # Arrange
    valid_id = ObjectId()
    valid_id_str = str(valid_id)

    # Mock the collection to return None (book state deleted)
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    monkeypatch.setattr(routes, "get_book_collection", lambda: mock_collection)

    response = client.get(f"/books/{valid_id_str}")
    assert response.status_code == 404
    assert response.content_type == "application/json"
    assert "Book not found" in response.get_json()["error"]


def test_invalid_urls_return_404(client):
    # Test invalid URL
    response = client.get("/books/")
    assert response.status_code == 404
    assert response.content_type == "application/json"
    assert "404 Not Found" in response.get_json()["error"]


# ------------------------ Tests for DELETE --------------------------------------------


def test_book_is_soft_deleted_on_delete_request(client):
    with patch("app.routes.books", books_database):
        # Send DELETE request with valid API header
        book_id = "1"
        headers = {"X-API-KEY": "test-key-123"}
        response = client.delete(f"/books/{book_id}", headers=headers)

        assert response.status_code == 204
        assert response.data == b""
        # check that the book's state has changed to deleted
        assert books_database[0]["state"] == "deleted"


def test_delete_empty_book_id(client):
    book_id = ""
    response = client.delete(f"/books/{book_id}")
    assert response.status_code == 404
    assert response.content_type == "application/json"
    assert "404 Not Found" in response.get_json()["error"]


def test_delete_invalid_book_id(client):
    headers = {"X-API-KEY": "test-key-123"}
    response = client.delete("/books/12341234", headers=headers)
    assert response.status_code == 404
    assert response.content_type == "application/json"
    assert "Book not found" in response.get_json()["error"]


def test_book_database_is_initialized_for_delete_book_route(client):
    with patch("app.routes.books", None):
        headers = {"X-API-KEY": "test-key-123"}
        response = client.delete("/books/1", headers=headers)
        assert response.status_code == 500
        assert "Book collection not initialized" in response.get_json()["error"]


# ------------------------ Tests for PUT --------------------------------------------


def test_update_book_request_returns_correct_status_and_content_type(client):
    with patch("app.routes.books", books_database):

        test_book = {
            "title": "Test Book",
            "author": "AN Other",
            "synopsis": "Test Synopsis",
        }
        # Define the valid headers, including the API key that matches conftest.py
        valid_headers = {"X-API-KEY": "test-key-123"}

        # send PUT request
        response = client.put("/books/1", json=test_book, headers=valid_headers)

        # Check response status code and content type
        assert response.status_code == 200
        assert response.content_type == "application/json"


def test_update_book_request_returns_required_fields(client):
    with patch("app.routes.books", books_database):
        test_book = {
            "title": "Test Book",
            "author": "AN Other",
            "synopsis": "Test Synopsis",
        }
        # Define the valid headers, including the API key that matches conftest.py
        valid_headers = {"X-API-KEY": "test-key-123"}

        # Send PUT request
        response = client.put("/books/1", json=test_book, headers=valid_headers)
        response_data = response.get_json()

        # Check that required fields are in the response data
        required_fields = ["title", "synopsis", "author", "links"]
        for field in required_fields:
            assert field in response_data, f"{field} not in response_data"


def test_update_book_replaces_whole_object(client):
    book_to_be_changed = {
        "id": "1",
        "title": "Original Title",
        "author": "Original Author",
        "synopsis": "Original Synopsis",
        "links": {
            "self": "link to be changed",
            "reservations": "link to be changed",
            "reviews": "link to be changed",
        },
    }
    # Patch the books list with just this book (no links)
    with patch("app.routes.books", [book_to_be_changed]):
        updated_data = {
            "title": "Updated Title",
            "author": "Updated Author",
            "synopsis": "Updated Synopsis",
        }
        # Define the valid headers, including the API key that matches conftest.py
        valid_headers = {"X-API-KEY": "test-key-123"}
        response = client.put("/books/1", json=updated_data, headers=valid_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert "links" in data
        assert "/books/1" in data["links"]["self"]
        assert "/books/1/reservations" in data["links"]["reservations"]
        assert "/books/1/reviews" in data["links"]["reviews"]

        # Verify other fields were updated
        assert data["title"] == "Updated Title"
        assert data["author"] == "Updated Author"
        assert data["synopsis"] == "Updated Synopsis"


def test_update_book_sent_with_invalid_book_id(client):
    with patch("app.routes.books", books_database):
        test_book = {
            "title": "Some title",
            "author": "Some author",
            "synopsis": "Some synopsis",
        }
        # Define the valid headers, including the API key that matches conftest.py
        valid_headers = {"X-API-KEY": "test-key-123"}
        response = client.put("/books/999", json=test_book, headers=valid_headers)
        assert response.status_code == 404
        assert "Book not found" in response.get_json()["error"]


def test_book_database_is_initialized_for_update_book_route(client):
    with patch("app.routes.books", None):
        test_book = {
            "title": "Test Book",
            "author": "AN Other",
            "synopsis": "Test Synopsis",
        }
        # Define the valid headers, including the API key that matches conftest.py
        valid_headers = {"X-API-KEY": "test-key-123"}
        # Send PUT request
        response = client.put("/books/1", json=test_book, headers=valid_headers)
        assert response.status_code == 500
        assert "Book collection not initialized" in response.get_json()["error"]


def test_update_book_check_request_header_is_json(client):

    response = client.put(
        "/books/1",
        data="This is not a JSON object",
        headers={"content-type": "text/plain", "X-API-KEY": "test-key-123"},
    )

    assert response.status_code == 415
    assert "Request must be JSON" in response.get_json()["error"]


def test_update_book_with_invalid_json_content(client):
    # Define the valid headers, including the API key that matches conftest.py
    valid_headers = {"X-API-KEY": "test-key-123"}

    # This should trigger a TypeError
    response = client.put(
        "/books/1", json="This is not a JSON object", headers=valid_headers
    )

    assert response.status_code == 400
    assert "JSON payload must be a dictionary" in response.get_json()["error"]


def test_update_book_sent_with_missing_required_fields(client):
    test_book = {
        "author": "AN Other"
        # missing 'title' and 'synopsis'
    }
    # Define the valid headers, including the API key that matches conftest.py
    valid_headers = {"X-API-KEY": "test-key-123"}

    response = client.put("/books/1", json=test_book, headers=valid_headers)

    assert response.status_code == 400
    response_data = response.get_json()
    assert "error" in response_data
    assert "Missing required fields: title, synopsis" in response.get_json()["error"]


# ------------------------ Tests for HELPER FUNCTIONS -------------------------------------


def test_add_book_response_contains_absolute_urls(client, monkeypatch):
    # Arrange
    test_book_payload = {
        "title": "Append Test Book",
        "author": "AN Other II",
        "synopsis": "Test Synopsis",
    }
    valid_headers = {"X-API-KEY": "test-key-123"}

    # A. Mock the result of the insert operation
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = ObjectId()
    book_id_str = str(mock_insert_result.inserted_id)

    # B. Mock the book as it would look coming from the database, *before* formatting.
    #    It has an `_id` and RELATIVE links.
    mock_book_from_db = test_book_payload.copy()
    mock_book_from_db["_id"] = mock_insert_result.inserted_id
    mock_book_from_db["links"] = {"self": f"/books/{book_id_str}"}

    # C. Mock the collection object
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = mock_book_from_db

    # D. Mock the helper function that gets called
    mock_insert_helper = MagicMock(return_value=mock_insert_result)

    # E. Apply all patches to isolate the route from the database
    monkeypatch.setattr("app.routes.get_book_collection", lambda: mock_collection)
    monkeypatch.setattr("app.routes.insert_book_to_mongo", mock_insert_helper)

    # Act
    response = client.post("/books", json=test_book_payload, headers=valid_headers)

    # Assert
    assert response.status_code == 201, f"Expected 201 but got {response.status_code}"

    response_data = response.get_json()

    assert "links" in response_data
    assert "self" in response_data["links"]

    expected_link_start = f"http://localhost/books/{book_id_str}"
    actual_link = response_data["links"]["self"]

    assert (
        actual_link == expected_link_start
    ), f"Link did not have the correct absolute URL. Expected '{expected_link_start}', got '{actual_link}'"  # pylint: disable=line-too-long
    assert actual_link is not None, "Response JSON must contain a 'links' object"


@patch("app.services.book_service.find_books")
def test_append_host_to_links_in_get(mock_find_books, client):

    # ARRANGE: Provide sample data for the mock to return
    mock_find_books.return_value = [
        {
            "_id": "123",
            "title": "A Test Book",
            "author": "The Tester",
            "synopsis": "A book for testing.",
            "links": {
                "self": "/books/123",
                "reservations": "/books/123",
                "reviews": "/books/123",
            },
        }
    ]

    # ACT
    response = client.get("/books")
    response_data = response.get_json()

    # ASSERT
    assert response.status_code == 200

    book = response_data["items"][0]
    assert response.headers["content-type"] == "application/json"
    assert isinstance(response_data, dict)
    assert "total_count" in response_data
    assert "items" in response_data
    # response_data["items"]["links"]["self"]
    for book in response_data["items"]:
        new_book_id = book.get("id")
        assert book["links"]["self"].startswith("http://localhost")
        assert book["links"]["self"] == "http://localhost/books/123"
        assert book["links"]["reservations"].startswith("http://localhost")
        assert book["links"]["reviews"].startswith("http://localhost")
        assert book["links"]["self"].endswith(f"books/{new_book_id}")


def test_append_host_to_links_in_get_book(client, monkeypatch):
    """
    GIVEN a request for a book ID
    WHEN the database and helper functions are mocked
    THEN the route handler correctly calls its dependencies and formats the final JSON response.
    """
    # Arrange: define constants and mock return values
    book_id = ObjectId()
    book_id_str = str(book_id)
    book_from_db = {
        "_id": book_id,
        "title": "Some Title",
        "author": "Some Author",
        "synopsis": "Foo bar.",
        "state": "active",
        "links": {},
    }
    # Mock the external dependencies
    fake_collection = MagicMock()
    fake_collection.find_one.return_value = book_from_db
    # Patch the function that the route uses to get the collection
    monkeypatch.setattr(routes, "get_book_collection", lambda: fake_collection)

    # mock append_hostname helper, define its output
    mock_appender = MagicMock(
        return_value={
            **book_from_db,
            "links": {
                "self": f"http://localhost/books/{book_id_str}",
                "reservations": f"http://localhost/books/{book_id_str}",
                "reviews": f"http://localhost/books/{book_id_str}",
            },
        }
    )
    monkeypatch.setattr(routes, "append_hostname", mock_appender)

    # ACT
    response = client.get(f"/books/{book_id_str}")

    # Assert
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["id"] == book_id_str
    assert "links" in response_data
    # Assert the final JSON is correct (based on the mock_appender's return value)
    assert (
        response_data.get("links", {}).get("self")
        == f"http://localhost/books/{book_id_str}"
    )

    # Now specifically check the 'self' link
    self_link = response_data["links"]["self"]
    reservations_link = response_data["links"]["reservations"]
    reviews_link = response_data["links"]["reviews"]
    assert self_link, "Expected a 'self' link in the response"
    assert reservations_link
    assert reviews_link

    # By default Flask's test_client serves on http://localhost/
    assert self_link.startswith(
        "http://localhost"
    ), f"Expected the link to start with 'http://localhost', got {self_link!r}"

    # And it must end with the resource path
    assert self_link.endswith(
        f"/books/{book_id_str}"
    ), f"Expected link to end with '/books/{book_id_str}', got {self_link!r}"
    # Assert the internal behavior was correct
    expected_query = {"_id": book_id, "state": {"$ne": "deleted"}}
    fake_collection.find_one.assert_called_once_with(expected_query)
    mock_appender.assert_called_once_with(book_from_db, ANY)


def test_append_host_to_links_in_put(client):

    test_book = {
        "title": "Test Book",
        "author": "AN Other",
        "synopsis": "Test Synopsis",
    }
    # Define the valid headers, including the API key that matches conftest.py
    valid_headers = {"X-API-KEY": "test-key-123"}

    response = client.put("/books/1", json=test_book, headers=valid_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    # Get the response data, the ID and links
    response_data = response.get_json()
    book_id = response_data.get("id")
    links = response_data.get("links")

    assert book_id is not None, "Response JSON must contain an 'id'"
    assert links is not None, "Response JSON must contain a 'links' object"

    self_link = links.get("self")
    assert self_link is not None, "'links' object must contain a 'self' link"

    expected_link_start = "http://localhost"
    assert self_link.startswith(
        expected_link_start
    ), f"Link should start with the test server's hostname '{expected_link_start}'"

    expected_path = f"/books/{book_id}"
    assert self_link.endswith(
        expected_path
    ), f"Link should end with the resource path '{expected_path}'"


def test_get_book_collection_handles_connection_failure():
    with patch("app.datastore.mongo_db.MongoClient") as mock_client:
        # Set the side effect to raise a ServerSelectionTimeoutError
        mock_client.side_effect = ServerSelectionTimeoutError("Mock Connection Timeout")

        app = create_app()
        with app.app_context():  # <-- Push the app context here
            with pytest.raises(Exception) as exc_info:
                get_book_collection()

        assert "Could not connect to MongoDB: Mock Connection Timeout" in str(
            exc_info.value
        )
