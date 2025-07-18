# pylint: disable=missing-docstring
"""
Tests for API security features, such as API key authentication.
"""

# -------------- POST --------------------------

def test_create_book_fails_without_api_key(client, monkeypatch):

    # 1. Stub out any external dependencies
    monkeypatch.setattr("app.routes.get_book_collection", lambda: None)
    monkeypatch.setattr(
        "app.routes.insert_book_to_mongo", lambda book, collection: None
    )
    monkeypatch.setattr("app.routes.append_hostname", lambda book, host: book)

    # 2. Build a valid payload, but don't include the header
    payload = {
        "title": "A Test Book",
        "synopsis": "A test synopsis.",
        "author": "Tester McTestFace",
    }

    # 3. Hit the endpoint without Authorization header
    response = client.post("/books", json=payload)
    print("Response:", response.get_data(as_text=True))
    print("Status code", response.status_code)

    # 4. Assert that you got a 401 back
    assert response.status_code == 401
    assert "Invalid or missing API Key" in response.json["error"]["message"]


def test_create_book_succeeds_with_valid_api_key(client, monkeypatch):
    """
    GIVEN a Flask application configured for testing
    WHEN a POST request is made to '/books' WITH a valid API key in the headers
    THEN check that the response is 201 Created
    """
    # We still need to patch the database for this unit test
    monkeypatch.setattr("app.routes.get_book_collection", lambda: None)
    monkeypatch.setattr(
        "app.routes.insert_book_to_mongo", lambda book, collection: None
    )
    monkeypatch.setattr("app.routes.append_hostname", lambda book, host: book)

    # The payload does NOT contain the key.
    valid_payload = {
        "title": "A Real Book",
        "synopsis": "It's real.",
        "author": "A. Real Person",
    }

    # The headers dictionary contains the key.
    valid_headers = {
        "X-API-KEY": "test-key-123"  # This must match the key in conftest.py
    }

    # Pass the headers dictionary to the `headers` argument.
    response = client.post("/books", json=valid_payload, headers=valid_headers)

    assert response.status_code == 201

# -------------- PUT --------------------------

def test_update_book_fails_without_api_key(monkeypatch, client):
    """Should return 401 if no API key is provided."""

    monkeypatch.setattr("app.routes.books", [])

    payload = {
        "title": "New Title",
        "synopsis": "New Synopsis",
        "author": "New Author"
    }

    response = client.put("/books/abc123", json=payload)

    assert response.status_code == 401
    assert "API Key" in response.json["error"]["message"]


def test_update_book_succeeds_with_api_key(monkeypatch, client):
    """Test successful book update with valid API key."""

    # 1. Patch the books list
    test_books = [{
        "id": "abc123",
        "title": "Old Title",
        "synopsis": "Old Synopsis",
        "author": "Old Author"
    }]
    monkeypatch.setattr("app.routes.books", test_books)

    # 2. Patch append_hostname to just return the book
    monkeypatch.setattr("app.routes.append_hostname", lambda book, host: book)

    # 3. Build request
    headers = {"X-API-KEY": "test-key-123"}
    payload = {
        "title": "New Title",
        "synopsis": "New Synopsis",
        "author": "New Author"
    }

    # 4. Call the endpoint
    response = client.put("/books/abc123", json=payload, headers=headers)

    # 5. Assert response
    assert response.status_code == 200
    assert response.json["title"] == "New Title"

# -------------- DELETE --------------------------
def test_delete_book_unauthorized(client):
    """
    WHEN a DELETE request is made without an API key
    THEN the response should be 401 Unauthorized
    """
    response = client.delete("/books/some-id")
    assert response.status_code == 401
    assert "Invalid or missing API Key" in response.json["error"]["message"]

def test_delete_book_authorized(client, monkeypatch):
    """
    WHEN a DELETE request is made with a valid API key
    THEN it should return 200 OK (or appropriate response)
    """
    monkeypatch.setattr("app.routes.books", [{"id": "some-id"}])

    headers = {"X-API-KEY": "test-key-123"}
    response = client.delete("/books/some-id", headers=headers)
    assert response.status_code == 204
