"""
Tests for the GET /books endpoint, specifically focusing on pagination logic.
"""

import pytest

@pytest.mark.parametrize("query_params, expected_error_msg", [
    ("?limit=-5", "cannot be negative"),
    ("?offset=-1", "cannot be negative"),
    ("?limit=abc", "must be integers"),
    ("?offset=abc", "must be integers"),
])
def test_get_books_with_invalid_params(client, query_params, expected_error_msg):
    """
    GIVEN any client
    WHEN a GET request is made to /books with invalid pagination parameters
    THEN it should return a 400 Bad Request wiht a relevant error message.
    """
    response = client.get(f"/books{query_params}")
    json_data = response.get_json()

    assert response.status_code == 400
    assert "error" in json_data
    assert expected_error_msg in json_data["error"]
