# pylint: disable=missing-docstring

from unittest.mock import patch

import pytest
from pymongo.errors import ServerSelectionTimeoutError

from app import create_app
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


def test_add_book_creates_new_book(client, _insert_book_to_db):

    test_book = {
        "title": "Test Book",
        "author": "AN Other",
        "synopsis": "Test Synopsis",
    }

    # Define the valid headers, including the API key that matches conftest.py
    valid_headers = {"X-API-KEY": "test-key-123"}

    response = client.post("/books", json=test_book, headers=valid_headers)

    assert response.status_code == 201
    assert response.headers["content-type"] == "application/json"

    response_data = response.get_json()
    required_fields = ["id", "title", "synopsis", "author", "links"]
    # check that required fields are in the response data
    for field in required_fields:
        assert field in response_data, f"{field} not in response_data"


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
        headers=valid_headers,
    )

    assert response.status_code == 415
    assert "Request must be JSON" in response.get_json()["error"]


def test_500_response_is_json(client):
    test_book = {
        "title": "Valid Title",
        "author": "AN Other",
        "synopsis": "Test Synopsis",
    }
    # Define the valid headers, including the API key that matches conftest.py
    valid_headers = {"X-API-KEY": "test-key-123"}

    # Use patch to mock uuid module failing and throwing an exception
    with patch("uuid.uuid4", side_effect=Exception("An unexpected error occurred")):
        response = client.post("/books", json=test_book, headers=valid_headers)

        # Check the response code is 500
        assert response.status_code == 500

        assert response.content_type == "application/json"
        assert "An unexpected error occurred" in response.get_json()["error"]


# ------------------------ Tests for GET --------------------------------------------
def test_get_all_books_returns_all_books(client):
    response = client.get("/books")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    response_data = response.get_json()
    assert isinstance(response_data, dict)
    assert "total_count" in response_data
    assert "items" in response_data


def test_return_error_404_when_list_is_empty(client):
    with patch("app.routes.books", []):
        response = client.get("/books")
        assert response.status_code == 404
        assert "No books found" in response.get_json()["error"]


def test_get_books_returns_404_when_books_is_none(client):
    with patch("app.routes.books", None):
        response = client.get("/books")
        assert response.status_code == 404
        assert "No books found" in response.get_json()["error"]


def test_missing_fields_in_book_object_returned_by_database(client):
    with patch(
        "app.routes.books",
        [
            {
                "id": "1",
                "title": "The Great Adventure",
                "synopsis": "A thrilling adventure through the jungles of South America.",
                "author": "Jane Doe",
            },
            {"id": "2", "title": "Mystery of the Old Manor"},
            {
                "id": "3",
                "title": "The Science of Everything",
                "synopsis": "An in-depth look at the scientific principles that govern our world.",
            },
        ],
    ):
        response = client.get("/books")
        assert response.status_code == 500
        assert "Missing fields" in response.get_json()["error"]


# -------- Tests for filter GET /books by delete ----------------


def test_get_books_excludes_deleted_books_and_omits_state_field(client):
    # Add a book so we have a known ID
    with patch(
        "app.routes.books",
        [
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
                "state": "deleted",
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
            },
        ],
    ):
        response = client.get("/books")
        assert response.status_code == 200

        data = response.get_json()
        assert "items" in data
        books = data["items"]

        # Check right object is returned
        assert len(books) == 2
        for book in books:
            assert "state" not in book
        assert books[0].get("id") == "2"
        assert books[1].get("title") == "The Science of Everything"


# -------- Tests for GET a single resource ----------------


def test_get_book_returns_specified_book(client):
    # Test GET request using the book ID
    get_response = client.get("/books/1")
    assert get_response.status_code == 200
    assert get_response.content_type == "application/json"
    returned_book = get_response.get_json()
    assert returned_book["id"] == "1"
    assert returned_book["title"] == "The Great Adventure"


def test_get_book_not_found_returns_404(client):
    # Test GET request using invalid book ID
    response = client.get("/books/12341234")
    assert response.status_code == 404
    assert response.content_type == "application/json"
    assert "Book not found" in response.get_json()["error"]


def test_invalid_urls_return_404(client):
    # Test invalid URL
    response = client.get("/books/")
    assert response.status_code == 404
    assert response.content_type == "application/json"
    assert "404 Not Found" in response.get_json()["error"]


def test_book_database_is_initialized_for_specific_book_route(client):
    with patch("app.routes.books", None):
        response = client.get("/books/1")
        assert response.status_code == 500
        assert "Book collection not initialized" in response.get_json()["error"]


def test_get_book_returns_404_if_state_equals_deleted(client):
    book_id = "3"
    response = client.get(f"/books/{book_id}")
    assert response.status_code == 404
    assert response.content_type == "application/json"
    assert "Book not found" in response.get_json()["error"]


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


def test_append_host_to_links_in_post(client, _insert_book_to_db):
    # 1. Make a POST request
    test_book = {
        "title": "Append Test Book",
        "author": "AN Other II",
        "synopsis": "Test Synopsis",
    }
    # Define the valid headers, including the API key that matches conftest.py
    valid_headers = {"X-API-KEY": "test-key-123"}

    response = client.post("/books", json=test_book, headers=valid_headers)

    assert response.status_code == 201
    assert response.headers["content-type"] == "application/json"

    # 2. Get the response data
    response_data = response.get_json()
    new_book_id = response_data.get("id")
    links = response_data.get("links")

    assert new_book_id is not None, "Response JSON must contain an 'id'"
    assert links is not None, "Response JSON must contain a 'links' object"

    # 3. Assert the hostname in the generated links
    print(f"\n[TEST INFO] Links returned from API: {links}")
    self_link = links.get("self")
    assert self_link is not None, "'links' object must contain a 'self' link"
    # Check that the hostname from the simulated request ('localhost') was correctly prepended.
    expected_link_start = "http://localhost"
    assert self_link.startswith(
        expected_link_start
    ), f"Link should start with the test server's hostname '{expected_link_start}'"
    # Also check that the path is correct
    expected_path = f"/books/{new_book_id}"
    assert self_link.endswith(
        expected_path
    ), f"Link should end with the resource path '{expected_path}'"


def test_append_host_to_links_in_get(client):
    response = client.get("/books")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    # Get the response data
    response_data = response.get_json()
    assert isinstance(response_data, dict)
    assert "total_count" in response_data
    assert "items" in response_data

    # response_data["items"]["links"]["self"]
    for book in response_data["items"]:
        new_book_id = book.get("id")
        assert book["links"]["self"].startswith("http://localhost")
        assert book["links"]["reservations"].startswith("http://localhost")
        assert book["links"]["reviews"].startswith("http://localhost")
        assert book["links"]["self"].endswith(f"books/{new_book_id}")


def test_append_host_to_links_in_get_book(client):

    response = client.get("/books/1")

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
