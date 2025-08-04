# pylint: disable=missing-docstring, duplicate-code

from unittest.mock import ANY, MagicMock, patch

import pytest
from bson.objectid import ObjectId
from pymongo.errors import ServerSelectionTimeoutError

from tests.test_data import HEADERS, DUMMY_PAYLOAD

from app import create_app, routes
from app.datastore.mongo_db import get_book_collection


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


def test_append_host_to_links_in_put(monkeypatch, client):
    """
    GIVEN a successful PUT operation
    WHEN the response is being formatted
    THEN the `update_book` route must call the `append_hostname` helper.
    """

    test_book_id = str(ObjectId())
    test_payload = DUMMY_PAYLOAD

    # a) Set up the mock database flow
    book_doc_from_db = {"_id": ObjectId(test_book_id), **test_payload}
    mock_collection = MagicMock()
    mock_collection.replace_one.return_value.matched_count = 1
    mock_collection.find_one.return_value = book_doc_from_db
    monkeypatch.setattr("app.routes.get_book_collection", lambda: mock_collection)

    with patch("app.routes.append_hostname") as mock_append_hostname:
        mock_append_hostname.side_effect = lambda book, host: book

        # --- 2. ACT ---
        response = client.put(
            f"/books/{test_book_id}", json=test_payload, headers=HEADERS["VALID"]
        )

        assert response.status_code == 200
        mock_append_hostname.assert_called_once()
        call_args, call_kwargs = ( # pylint: disable=unused-variable
            mock_append_hostname.call_args
        )
        book_arg = call_args[0]
        host_arg = call_args[1]

        assert "links" in book_arg
        assert book_arg["links"]["self"] == f"/books/{test_book_id}"
        assert host_arg == "http://localhost"  # Flask test client default


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
