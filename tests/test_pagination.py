"""
Tests for the GET /books endpoint, specifically focusing on pagination logic.
"""

import pytest

@pytest.mark.parametrize(
    "query_params, expected_error_msg",
    [
        ("?limit=-5", "cannot be negative"),
        ("?limit=abc", "must be integers"),
        ("?offset=abc", "must be integers"),
    ],
)
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

invalid_offset_values = [-1, 2001]

@pytest.mark.parametrize("invalid_offset", invalid_offset_values)
def test_get_books_fails_for_out_of_range_offset(client, invalid_offset):
    """
    GIVEN an offset that is either negative or exceeds the configured max
    WHEN a GET request is made to /books with that offset
    THEN it should return a 400 Bad Request with the correct error message.
    """
    # Arrange
    # Get the max_offset from the app's config to build the expected message.
    max_offset = client.application.config['MAX_OFFSET']
    expected_error_msg = f"Offset has to be a positive number no greater then {max_offset}."

    # Act
    response = client.get(f"/books?offset={invalid_offset}")
    json_data = response.get_json()

    # Assert
    assert response.status_code == 400
    assert "error" in json_data
    assert json_data["error"] in expected_error_msg
