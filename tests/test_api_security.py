"""
Tests for API security features, such as API key authentication.
"""

def test_create_book_fails_without_api_key(test_client, monkeypatch):
    """
    GIVEN a Flask application configured for testing
    WHEN a POST request is made to '/books' WITHOUT an API key in the headers
    THEN check that the response is 401 Unauthorized
    """
    # 1. Stub out any external dependencies
    monkeypatch.setattr("app.routes.get_book_collection", lambda: None)
    monkeypatch.setattr("app.routes.insert_book_to_mongo", lambda book, collection: None)
    monkeypatch.setattr("app.routes.append_hostname", lambda book, host: book)

    # 2. Build a valid payload, but don't include the header
    payload = {
        "title": "A Test Book",
        "synopsis": "A test synopsis.",
        "author": "Tester McTestFace"
    }

    # 3. Hit the endpoint without Authorization header
    response = test_client.post("/books", json=payload)
    print("Response:", response.get_data(as_text=True))
    print("Status code", response.status_code)

    # 4. Assert that you got a 401 back
    assert response.status_code == 401
    assert "Invalid or missing API Key" in response.json["error"]["message"]



def test_create_book_succeeds_with_valid_api_key(test_client, monkeypatch):
    """
    GIVEN a Flask application configured for testing
    WHEN a POST request is made to '/books' WITH a valid API key in the headers
    THEN check that the response is 201 Created
    """
    # We still need to patch the database for this unit test
    monkeypatch.setattr("app.routes.get_book_collection", lambda: None)
    monkeypatch.setattr("app.routes.insert_book_to_mongo", lambda book, collection: None)
    monkeypatch.setattr("app.routes.append_hostname", lambda book, host: book)

    # The payload does NOT contain the key.
    valid_payload = {
        "title": "A Real Book",
        "synopsis": "It's real.",
        "author": "A. Real Person"
    }

    # The headers dictionary contains the key.
    valid_headers = {
        "X-API-KEY": "test-key-123" # This must match the key in conftest.py
    }

    # Pass the headers dictionary to the `headers` argument.
    response = test_client.post("/books", json=valid_payload, headers=valid_headers)

    assert response.status_code == 201
