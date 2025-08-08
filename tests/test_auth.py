"""Tests for auth/JWT upgrade"""

import bcrypt
import pytest

from app import mongo


def test_register_with_valid_data(client, users_db_setup):
    """GIVEN a clean users collection
    WHEN a POST request is sent to /auth/register with new user data
    THEN the response should be 201 CREATED and the user should exist in the DB"""
    _ = users_db_setup  # pylint: disable=unused-variable

    # Arrange
    new_user_data = {"email": "newuser@example.com", "password": "a-secure-password"}
    # ACT
    response = client.post("/auth/register", json=new_user_data)

    # Verify the user was actually created in the database
    assert response.status_code == 201
    user_in_db = mongo.db.users.find_one({"email": "newuser@example.com"})
    assert user_in_db is not None
    assert "password_hash" in user_in_db
    # You can even check if the password hashes match!
    assert bcrypt.checkpw(
        b"a-secure-password", user_in_db["password_hash"].encode("utf-8")
    )


def test_register_with_duplicate_email(client, users_db_setup):
    """
    GIVEN a user already exists in the database
    WHEN a POST request is sent to /auth/register with the same email
    THEN the response should be 409 Conflict"""
    _ = users_db_setup  # pylint: disable=unused-variable

    # Arrange
    existing_user_data = {
        "email": "newuser@example.com",
        "password": "a-secure-password",
    }
    client.post("/auth/register", json=existing_user_data)
    # sanity-check
    user_in_db = mongo.db.users.find_one({"email": "newuser@example.com"})
    assert user_in_db is not None
    assert "password_hash" in user_in_db

    # Act: try to register with the same email again
    response = client.post("/auth/register", json=existing_user_data)

    # Assert
    assert response.status_code == 409
    assert "email is already registered" in response.get_json()["message"].lower()


def test_register_fails_with_empty_json(client, users_db_setup):
    """
    When a POST is sent with an empty JSON,
    it returns a 400 and an error message
    """
    _ = users_db_setup  # pylint: disable=unused-variable

    # Arrange
    json_body = ""

    # Act
    response = client.post(
        "/auth/register",
        json=json_body,
    )

    assert response.status_code == 400
    assert "request body cannot be empty" in response.get_json()["message"].lower()


def test_request_fails_with_invalid_json(client, users_db_setup):
    """
    When a POST is sent with an empty JSON,
    it returns a 400 and an error message
    """
    _ = users_db_setup  # pylint: disable=unused-variable

    # Arrange
    invalid_json_string = "this is not json"

    # Act
    response = client.post(
        "/auth/register", data=invalid_json_string, content_type="application/json"
    )

    assert response.status_code == 400
    assert "invalid json format" in response.get_json()["message"].lower()


@pytest.mark.parametrize(
    "payload, expected_message",  # Define the names of the variables for the test
    [
        ({"password": "a-password"}, "Email and password are required"),  # 1st test
        ({"email": "test@example.com"}, "Email and password are required"),  # 2nd test
        ({}, "Request body cannot be empty"),  # 3rd test
    ],
)
def test_request_fails_with_missing_fields(
    client, users_db_setup, payload, expected_message
):
    """
    GIVEN a payload that is missing a required field (email or password)
    WHEN a POST request is sent to /auth/register
    THEN the response should be 400 Bad Request with an appropriate error message.
    """
    _ = users_db_setup  # pylint: disable=unused-variable

    # Act
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 400
    response_data = response.get_json()
    assert expected_message in response_data["message"]

@pytest.mark.parametrize("invalid_email", [
    "not-an-email",           # Just a string
    "test@.com",              # Missing domain name
    "test@domain.",           # Missing top-level domain
    "test@domaincom",         # Missing dot in domain
    "test @ domain.com"       # Contains spaces
])
def test_register_fails_with_invalid_email(client, users_db_setup, invalid_email):
    """
    GIVEN a Flask application client
    WHEN a POST request is made to /auth/register with an invalid email format
    THEN the response status code should be 400 (Bad Request)
    AND the response JSON should contain an appropriate error message.
    """
    _ = users_db_setup  # pylint: disable=unused-variable

    # Arrange
    new_user_data = {
        "email": invalid_email, 
        "password": "a-secure-password"
    }
    # ACT
    response = client.post("/auth/register", json=new_user_data)

    # assert
    assert response.status_code == 400
    data = response.get_json()
    assert isinstance(data, dict), "Expected JSON body"
    assert "message" in data
    assert "message" in data, "The error response should contain a 'message' key"
