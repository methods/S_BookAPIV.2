# pylint: disable=missing-docstring
"""
Tests for API security features, such as API key authentication.
"""
import logging

import pytest

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
    # Patch the database
    monkeypatch.setattr("app.routes.get_book_collection", lambda: None)
    monkeypatch.setattr(
        "app.routes.insert_book_to_mongo", lambda book, collection: None
    )
    monkeypatch.setattr("app.routes.append_hostname", lambda book, host: book)

    response = client.post("/books", json=DUMMY_PAYLOAD, headers=HEADERS["VALID"])

    assert response.status_code == 201


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

    response = client.put("/books/abc123", json=DUMMY_PAYLOAD, headers=HEADERS["INVALID"])
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
    WHEN a DELETE request is made with a valid API key
    THEN it should return 200 OK (or appropriate response)
    """
    monkeypatch.setattr("app.routes.books", [{"id": "some-id"}])

    response = client.delete("/books/some-id", headers=HEADERS["VALID"])
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
