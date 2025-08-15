# pylint: disable=redefined-outer-name
"""
Test suite for decorators

To test the decorator in isolation, we'll create a tiny, temporary Flask app inside out test file. 

This app will have a single, simple route that does nothing but apply our decorator. 
This way, we know that any success or failure is due to the decorator itself, not other application code. # pylint: disable=line-too-long
"""
import pytest
from flask import Flask, g, jsonify

from app.utils.decorators import require_jwt

# A dummy secret key for testing
TEST_SECRET_KEY = "test-secret-key"

# Dummy route we'll protect
@require_jwt
def protected_route():
    """
    A minimal protected route function
    decorated with require_jwt we are testing

    Returns: the current user's email from g.current_user as JSON
    The idea is: if the decorator runs and attaches g.current_user, the route will be able to read it and return an email. If the decorator blocks the request (bad/missing token), the route body never runs. # pylint: disable=line-too-long
    """
    return jsonify({"email": g.current_user["email"]})

@pytest.fixture
def client():
    """
    Creates a minimal app and
    a test client
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = TEST_SECRET_KEY
    # register protected_route at /protected
    app.add_url_rule("/protected", view_func=protected_route)
    with app.test_client() as test_client:
        yield test_client


def test_require_jwt_authorization_header_missing(client):
    """
    GIVEN a request to a protected endpoint
    WHEN the Authorization header is missing
    THEN it should return a 401 Unauthorized error
    """
    # Act
    response = client.get("/protected")
    data = response.get_json()

    # Assert
    assert response.status_code == 401
    assert data["error"] == "Authorization header missing"

@pytest.mark.parametrize(
    "auth_header",
    [
        "Bearer",          # Just the word "Bearer"
        "Token 12345",     # Wrong schema word ("Token" instead of "Bearer")
        "Bearer token1 token2", # Too many parts
        "JustAToken",      # Only one part
    ],
)
def test_require_jwt_malformed_header(client, auth_header):
    """
    GIVEN a request to a protected endpoint
    WHEN the Authorization header is malformed
    THEN it should return a 401 Unauthorized error
    """

    # Act
    response = client.get("/protected", headers= {"Authorization": auth_header})
    data = response.get_json()

    # Assert
    assert response.status_code == 401
    assert data["error"] == "Malformed Authorization header"
