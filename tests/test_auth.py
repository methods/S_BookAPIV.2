"""Tests for auth/JWT upgrade"""

from unittest.mock import patch

import jwt
import pytest
from conftest import (PLAIN_PASSWORD,  # pylint: disable=import-error
                      TEST_USER_ID)

from app import bcrypt, mongo

# -------- /auth/register TESTS ---------


def test_register_with_valid_data(client, mongo_setup):
    """GIVEN a clean users collection
    WHEN a POST request is sent to /auth/register with new user data
    THEN the response should be 201 CREATED and the user should exist in the DB"""
    _ = mongo_setup

    # Arrange
    new_user_data = {"email": "newuser@example.com", "password": "a-secure-password"}
    # ACT
    response = client.post("/auth/register", json=new_user_data)

    # Verify the user was actually created in the database
    assert response.status_code == 201
    user_in_db = mongo.db.users.find_one({"email": "newuser@example.com"})
    assert user_in_db is not None
    assert "password" in user_in_db
    assert "role" in user_in_db
    assert user_in_db["role"] == "user"
    # Check if the password hashes match!
    assert bcrypt.check_password_hash(user_in_db["password"], "a-secure-password")


def test_register_with_duplicate_email(client, mongo_setup):
    """
    GIVEN a user already exists in the database
    WHEN a POST request is sent to /auth/register with the same email
    THEN the response should be 409 Conflict"""
    _ = mongo_setup

    # Arrange
    existing_user_data = {
        "email": "newuser@example.com",
        "password": "a-secure-password",
    }
    client.post("/auth/register", json=existing_user_data)
    # sanity-check
    user_in_db = mongo.db.users.find_one({"email": "newuser@example.com"})
    assert user_in_db is not None
    assert "password" in user_in_db

    # Act: try to register with the same email again
    response = client.post("/auth/register", json=existing_user_data)

    # Assert
    assert response.status_code == 409
    assert "email is already registered" in response.get_json()["message"].lower()


def test_register_fails_with_empty_json(client, mongo_setup):
    """
    When a POST is sent with an empty JSON,
    it returns a 400 and an error message
    """
    _ = mongo_setup

    # Arrange
    json_body = ""

    # Act
    response = client.post(
        "/auth/register",
        json=json_body,
    )

    assert response.status_code == 400
    assert "request body cannot be empty" in response.get_json()["message"].lower()


def test_request_fails_with_invalid_json(client, mongo_setup):
    """
    When a POST is sent with an empty JSON,
    it returns a 400 and an error message
    """
    _ = mongo_setup

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
    client, mongo_setup, payload, expected_message
):
    """
    GIVEN a payload that is missing a required field (email or password)
    WHEN a POST request is sent to /auth/register
    THEN the response should be 400 Bad Request with an appropriate error message.
    """
    _ = mongo_setup

    # Act
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 400
    response_data = response.get_json()
    assert expected_message in response_data["message"]


@pytest.mark.parametrize(
    "invalid_email",
    [
        "not-an-email",  # Just a string
        "test@.com",  # Missing domain name
        "test@domain.",  # Missing top-level domain
        "test@domaincom",  # Missing dot in domain
        "test @ domain.com",  # Contains spaces
    ],
)
def test_register_fails_with_invalid_email(client, mongo_setup, invalid_email):
    """
    GIVEN a Flask application client
    WHEN a POST request is made to /auth/register with an invalid email format
    THEN the response status code should be 400 (Bad Request)
    AND the response JSON should contain an appropriate error message.
    """
    _ = mongo_setup  # pylint: disable=unused-variable

    # Arrange
    new_user_data = {"email": invalid_email, "password": "a-secure-password"}
    # ACT
    response = client.post("/auth/register", json=new_user_data)

    # assert
    assert response.status_code == 400
    data = response.get_json()
    assert isinstance(data, dict), "Expected JSON body"
    assert "message" in data
    assert "message" in data, "The error response should contain a 'message' key"


# ---------- /auth/login -----------------


def test_login_user_returns_jwt_for_valid_credentials(
    test_app, client, seeded_user_in_db
):
    """
    GIVEN a user exists in the database (via seeded_user_in_db fixture)
    WHEN a POST request is sent to /auth/login with correct credentials
    THEN a 200 response with a valid JWT is returned
    """
    # Arrange
    _ = seeded_user_in_db

    login_credentials = {
        "email": "testuser@example.com",
        "password": PLAIN_PASSWORD,
    }  # plain-text password

    # ACT
    response = client.post("/auth/login", json=login_credentials)
    data = response.get_json()

    # Assert
    assert response.status_code == 200
    assert "token" in data

    with test_app.app_context():
        # check token: we need the SECRET_KEY from the app config to decode it.
        payload = jwt.decode(
            data["token"], test_app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
        )
        assert payload["sub"] == TEST_USER_ID
        assert payload["role"] == "user"


def test_login_user_fails_for_wrong_password(client, seeded_user_in_db):
    """
    GIVEN a user exists in the database
    WHEN a POST request is sent to /auth/login with an incorrect password
    THEN a 401 Unauthorized response is returned
    """
    # Arrange
    _ = seeded_user_in_db

    login_credentials = {"email": "testuser@example.com", "password": "wrong-password"}

    # Act
    response = client.post("/auth/login", json=login_credentials)

    # Assert
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid credentials"


def test_login_user_fails_for_nonexistent_user(client, seeded_user_in_db):
    """
    GIVEN a database (with or without users)
    WHEN a POST request is sent to /auth/login for a user that doesn't exist
    THEN a 401 Unauthorized response is returned
    """
    # Arrange
    _ = seeded_user_in_db

    login_credentials = {"email": "ghost@example.com", "password": "any-password"}

    # Act
    response = client.post("/auth/login", json=login_credentials)

    # Assert
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid credentials"


@pytest.mark.parametrize(
    "payload, expected_message",
    [
        ("null", "Email and password are required"),  # 'if not data'
        ({}, "Email and password are required"),  # empty JSON object
        (
            {"password": "a-password"},
            "Email and password are required",
        ),  # Missing email
        (
            {"email": "test@example.com"},
            "Email and password are required",
        ),  # Missing password
    ],
    ids=["null_payload", "empty_payload", "missing_email", "missing_password"],
)
def test_login_user_fails_with_missing_data(client, payload, expected_message):
    """
    GIVEN a test client
    WHEN a POST request is sent to /auth/login with incomplete data
    THEN the response should be 400 BAD REQUEST with a specific error message.
    """
    # Act
    # For the special 'null' case, we send it as raw data.
    # For all other cases (which are dicts), we send it as json.
    if isinstance(payload, str):
        response = client.post(
            "/auth/login", data=payload, content_type="application/json"
        )
    else:
        response = client.post("/auth/login", json=payload)

    data = response.get_json()

    # Assert
    assert response.status_code == 400
    assert data["error"] == expected_message


def test_login_handles_jwt_encoding_error(client, seeded_user_in_db):
    """
    GIVEN a valid user is logging in
    WHEN the internal PyJWT library fails to encode the token
    THEN the server should catch the specific PyJWTError and return a 500
    """
    # Arrange
    _ = seeded_user_in_db
    login_credentials = {
        "email": "testuser@example.com",
        "password": "a-secure-password",
    }
    # Patch jwt.encode() to be a mock
    with patch("app.routes.auth_routes.jwt.encode") as mock_jwt_encode:
        # Configure the mock to raise the specific exception we want to test
        mock_jwt_encode.side_effect = jwt.PyJWTError("Simulated library error")

        # Act
        response = client.post("/auth/login", json=login_credentials)
        data = response.get_json()

    # Assert
    assert response.status_code == 500
    assert data["error"] == "Token generation failed"
