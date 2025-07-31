# pylint: disable=missing-docstring
"""
Tests for API security features, such as API key authentication.
"""
import logging
from unittest.mock import MagicMock

import pytest
from bson.objectid import ObjectId

# A dictionary for headers to keep things clean
HEADERS = {
    "VALID": {"X-API-KEY": "test-key-123"},
    "INVALID": {"X-API-KEY": "This-is-the-wrong-key-12345"},
    "MISSING": {},
}

# A sample payload for POST/PUT requests
DUMMY_PAYLOAD = {
    "title": "A Test Book",
    "synopsis": "A test synopsis.",
    "author": "Tester McTestFace",
}

# -------------- LOGGING --------------------------


@pytest.mark.parametrize(
    "method, path",
    [
        ("post", "/books"),
        ("put", "/books/some-id"),
        ("delete", "/books/some-id"),
    ],
)
def test_invalid_api_key_logs_attempt_for_post_route(client, caplog, method, path):
    caplog.set_level(logging.WARNING)

    invalid_header = {"X-API-KEY": "This-is-the-wrong-key-12345"}

    response = getattr(client, method)(path, headers=invalid_header)

    assert response.status_code == 401
    assert "Unauthorized access attempt" in caplog.text
    assert "/books" in caplog.text


# -------------- POST --------------------------


def test_add_book_fails_with_missing_key(client, monkeypatch):

    # Mock external dependencies using monkeypatch
    monkeypatch.setattr("app.routes.get_book_collection", lambda: None)
    monkeypatch.setattr(
        "app.routes.insert_book_to_mongo", lambda book, collection: None
    )
    monkeypatch.setattr("app.routes.append_hostname", lambda book, host: book)

    # Hit the endpoint without Authorization header
    response = client.post("/books", json=DUMMY_PAYLOAD)

    # 4. Assert that you got a 401 back
    assert response.status_code == 401
    assert "API key is missing." in response.json["error"]["message"]


def test_add_book_succeeds_with_valid_key(client, monkeypatch):
    # Arrange
    # Create a fake result for the insert operation.
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = ObjectId()  # A new, fake ObjectId

    # Create a fake book document that would be returned by .find_one()
    mock_book_from_db = DUMMY_PAYLOAD.copy()
    mock_book_from_db["_id"] = mock_insert_result.inserted_id
    mock_book_from_db["links"] = {"self": "/books/..."}

    # Create a fake collection object with mocked methods.
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = mock_book_from_db

    # Patch get_book_collection to return our fake collection
    monkeypatch.setattr("app.routes.get_book_collection", lambda: mock_collection)
    # Patch insert_book_to_mongo to return our fake insert result
    monkeypatch.setattr(
        "app.routes.insert_book_to_mongo", lambda book, collection: mock_insert_result
    )
    monkeypatch.setattr("app.routes.append_hostname", lambda book, host: book)

    # Act
    response = client.post("/books", json=DUMMY_PAYLOAD, headers=HEADERS["VALID"])

    # Assert
    assert response.status_code == 201
    mock_collection.update_one.assert_called_once()
    mock_collection.find_one.assert_called_once()

    # Check the response body
    response_data = response.get_json()
    assert "id" in response_data
    assert "_id" not in response_data
    assert response_data["title"] == DUMMY_PAYLOAD["title"]


def test_add_book_fails_with_invalid_key(client):
    # ACT
    response = client.post("/books", json=DUMMY_PAYLOAD, headers=HEADERS["INVALID"])

    # ASSERT: Verify the server rejected the request as expected.
    assert response.status_code == 401
    assert "Invalid API key." in response.json["error"]["message"]


def test_add_book_fails_if_api_key_not_configured_on_the_server(client, test_app):
    # ARRANGE: Remove API_KEY from the test_app config
    test_app.config.pop("API_KEY", None)

    response = client.post("/books", json=DUMMY_PAYLOAD)

    assert response.status_code == 500
    assert "API key not configured on the server." in response.json["error"]["message"]


# -------------- PUT --------------------------
def test_update_book_succeeds_with_valid_api_key(monkeypatch, client):
    """Test successful book update with valid API key."""

    # 1. Patch the books list
    test_books = [
        {
            "id": "abc123",
            "title": "Old Title",
            "synopsis": "Old Synopsis",
            "author": "Old Author",
        }
    ]
    monkeypatch.setattr("app.routes.books", test_books)

    # 2. Patch append_hostname to just return the book
    monkeypatch.setattr("app.routes.append_hostname", lambda book, host: book)

    # 3. Call the endpoint with request details
    response = client.put("/books/abc123", json=DUMMY_PAYLOAD, headers=HEADERS["VALID"])

    # 4. Assert response
    assert response.status_code == 200
    assert response.json["title"] == "A Test Book"


def test_update_book_fails_with_missing_api_key(monkeypatch, client):
    """Should return 401 if no API key is provided."""

    monkeypatch.setattr("app.routes.books", [])

    response = client.put("/books/abc123", json=DUMMY_PAYLOAD)

    assert response.status_code == 401
    assert "API key is missing." in response.json["error"]["message"]


def test_update_book_fails_with_invalid_api_key(client, monkeypatch):
    monkeypatch.setattr("app.routes.books", [])

    response = client.put(
        "/books/abc123", json=DUMMY_PAYLOAD, headers=HEADERS["INVALID"]
    )
    # ASSERT: Verify the server rejected the request as expected.
    assert response.status_code == 401
    assert "Invalid API key." in response.json["error"]["message"]


def test_update_book_fails_if_api_key_not_configured_on_the_server(
    client, test_app, monkeypatch
):
    # ARRANGE: Remove API_KEY from the test_app config
    monkeypatch.setattr("app.routes.books", [])
    test_app.config.pop("API_KEY", None)

    response = client.put("/books/abc123", json=DUMMY_PAYLOAD)

    assert response.status_code == 500
    assert "API key not configured on the server." in response.json["error"]["message"]


# -------------- DELETE --------------------------
def test_delete_book_fails_with_invalid_api_key(client):
    """
    WHEN a DELETE request is made without an API key
    THEN the response should be 401 Unauthorized
    """
    response = client.delete("/books/some-id")
    assert response.status_code == 401
    assert "API key is missing." in response.json["error"]["message"]


def test_delete_book_succeeds_with_valid_api_key(client, monkeypatch):
    """
    GIVEN a valid API key
    WHEN a DELETE request is made to a valid book ID
    THEN the response should be 204 No Content
    """
    # Define what a successful result from the DB helper is
    successful_db_result = {"_id": "some-id", "state": "active"}

    monkeypatch.setattr(
        "app.routes.delete_book_by_id", lambda collection, book_id: successful_db_result
    )

    monkeypatch.setattr("app.routes.get_book_collection", lambda: "a fake collection")

    # Act
    valid_oid_string = "635c02a7a5f6e1e2b3f4d5e6"
    response = client.delete(f"/books/{valid_oid_string}", headers=HEADERS["VALID"])

    assert response.status_code == 204


def test_delete_book_fails_with_invalid_key(client):

    response = client.delete("/books/any-book-id", headers=HEADERS["INVALID"])

    # ASSERT: Verify the server rejected the request as expected.
    assert response.status_code == 401
    assert "Invalid API key." in response.json["error"]["message"]


def test_delete_book_fails_if_api_key_not_configured_on_the_server(client, test_app):
    test_app.config.pop("API_KEY", None)

    response = client.delete("/books/any-book-id")

    assert response.status_code == 500
    assert "API key not configured on the server." in response.json["error"]["message"]
