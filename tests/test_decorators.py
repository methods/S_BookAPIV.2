# pylint: disable=redefined-outer-name
"""
Test suite for decorators

To test the decorator in isolation, we'll create a tiny, temporary Flask app inside our test file.

This app will have a single, simple route that does nothing but apply our decorator.
This way, we know that any success or failure is due to the decorator itself, not other application code. # pylint: disable=line-too-long
"""

from unittest.mock import patch

import jwt
import pytest
from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, g, jsonify

from app.utils import decorators
from app.utils.decorators import require_jwt, require_admin

# A dummy secret key for testing
TEST_SECRET_KEY = "test-secret-key"


@pytest.fixture
def client():
    """
    Creates a minimal, isolated Flask app for unit testing the decorator.
    This is separate from the main app fixture in conftest.py.
    """
    # 1. Create a minimal Flask application
    app = Flask(__name__)
    # 2. Add the config the decorator needs
    app.config["JWT_SECRET_KEY"] = TEST_SECRET_KEY

    # 3. Create a protected route to test against
    @app.route("/protected")
    @require_jwt
    def protected_route():
        """
        A minimal protected route function
        decorated with require_jwt we are testing

        Returns: the current user's email from g.current_user as JSON
        """
        return jsonify(
            {"message": "success", "user_email": g.current_user.get("email")}
        )

    # 4. Yield the test client for this specific app
    with app.test_client() as test_client:
        yield test_client


def test_require_jwt_valid_token(client):
    """
    GIVEN a request to a protected endpoint
    WHEN the Authorization header contains a valid JWT
    THEN it should succeed and the route should have access to the user in g.current_user
    """
    # Arrange
    # 1. Create a dummy user ID
    user_id = ObjectId()
    dummy_user = {"_id": user_id, "email": "test@example.com"}

    # Mock the database call
    with patch(
        "app.extensions.mongo.db.users.find_one", return_value=dummy_user
    ), patch("app.utils.decorators.jwt.decode", return_value={"sub": str(user_id)}):

        token = "valid-token"
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        data = response.get_json()

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}. Response: {data}"  # pylint: disable=line-too-long
        assert data["message"] == "success"
        assert data["user_email"] == "test@example.com"


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
        "Bearer",  # Just the word "Bearer"
        "Token 12345",  # Wrong schema word ("Token" instead of "Bearer")
        "Bearer token1 token2",  # Too many parts
        "JustAToken",  # Only one part
    ],
)
def test_require_jwt_malformed_header(client, auth_header):
    """
    GIVEN a request to a protected endpoint
    WHEN the Authorization header is malformed
    THEN it should return a 401 Unauthorized error
    """
    # Act
    response = client.get("/protected", headers={"Authorization": auth_header})
    data = response.get_json()

    # Assert
    assert response.status_code == 401
    assert data["error"] == "Malformed Authorization header"


def test_require_jwt_expired_signature_error(client, monkeypatch):
    """
    GIVEN a request to a protected endpoint
    WHEN jwt.decode raises ExpiredSignatureError
    THEN it should return a 401 expiration error
    """

    # Arrange: patch jwt.decode where the decorator imports it
    def fake_decode(*args, **kwargs):
        raise jwt.ExpiredSignatureError()

    monkeypatch.setattr("app.utils.decorators.jwt.decode", fake_decode)

    # Act: send a request with any Bearer token
    response = client.get(
        "/protected", headers={"Authorization": "Bearer expired-token"}
    )
    data = response.get_json()

    # Assert
    assert response.status_code == 401
    assert data["error"] == "Token has expired"


def test_require_jwt_invalid_token_error(client):
    """
    GIVEN a request to a protected endpoint
    WHEN jwt.decode raises InvalidTokenError
    THEN it should return a 401 invalid token error
    """
    with patch("app.utils.decorators.jwt.decode", side_effect=jwt.InvalidTokenError()):
        response = client.get(
            "/protected", headers={"Authorization": "Bearer invalid-token"}
        )
        data = response.get_json()

        assert response.status_code == 401
        assert data is not None
        assert data["error"] == "Invalid token. Please log in again."


def test_require_jwt_missing_sub_claim(client):
    """
    GIVEN jwt.decode returns a payload without 'sub'
    WHEN we call the protected endpoint
    THEN the decorator should respond 401 with a missing-sub error
    """
    with patch("app.utils.decorators.jwt.decode", return_value={}):
        response = client.get(
            "/protected", headers={"Authorization": "Bearer <any-token>"}
        )
        data = response.get_json()

    assert response.status_code == 401
    assert data is not None
    assert data["error"] == "Token missing subject (sub) claim"


@pytest.mark.parametrize("exc", [InvalidId("bad id"), TypeError("bad type")])
def test_require_jwt_invalid_user_id_in_token_returns_401(client, monkeypatch, exc):
    """
    GIVEN jwt.decode returns a payload with a 'sub' value
    WHEN converting that 'sub' into an ObjectId raises InvalidId or TypeError
    THEN the endpoint should return 401 with a helpful error
    """

    # Arrange: make jwt.decode return a payload with a sub claim
    monkeypatch.setattr(
        "app.utils.decorators.jwt.decode", lambda *a, **k: {"sub": "some-value"}
    )

    # Arrange: make ObjectId(...) raise the desired exception
    def raise_exc(_value):
        raise exc

    monkeypatch.setattr("app.utils.decorators.ObjectId", raise_exc)

    # Act
    response = client.get("/protected", headers={"Authorization": "Bearer any-token"})
    data = response.get_json()

    # Assert
    assert response.status_code == 401
    assert data is not None
    assert data["error"] == "Invalid user id in token"


def test_require_jwt_user_not_found(client):
    """
    GIVEN a valid token with a user_id
    WHEN no matching user is found in the database
    THEN it should return 401 with 'User not found'
    """
    # 1. Create a valid JWT payload with a fake user_id
    fake_user_id = str(ObjectId())
    token = jwt.encode({"sub": fake_user_id}, TEST_SECRET_KEY, algorithm="HS256")

    # 2. Patch mongo to simulate "no user found"
    with patch.object(decorators.mongo.db.users, "find_one", return_value=None):
        # Act
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        data = response.get_json()

    # Assert
    assert response.status_code == 401
    assert data["error"] == "User not found"



# =======================================================
#       NEW FIXTURE AND TESTS FOR @require_admin
# =======================================================

@pytest.fixture
def admin_client():
    """
    Creates a minimal, isolated Flask app for unit testing the require_admin decorator. 
    """
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = TEST_SECRET_KEY # used by JWT libs; kept for parity

    # Protected route to test against
    @app.route("/admin-protected")
    @require_admin
    def admin_protected_route():
        return jsonify({"message": "admin access granted"})

    # This route is used to test the abort(403) case
    @app.errorhandler(403)
    def forbidden(e):
        return jsonify(error=str(e.description)), 403

    with app.test_client() as test_client:
        yield test_client


def test_require_admin_with_admin_role_succeeds(admin_client):
    """
    GIVEN a user with the 'admin' role
    WHEN they access a route protected by @require_admin
    THEN the request should succeed (200 OK)
    """
    # Arrange
    admin_user = {
        "_id": ObjectId(),
        "email": "admin@example.com",
        "role": "admin" # CRUCIAL
        }
    # Patch the dependencies of the inner decorator (@require_jwt)
    with patch("app.utils.decorators.jwt.decode", return_value={"sub": str(admin_user["_id"])}), \
        patch("app.utils.decorators.mongo.db.users.find_one", return_value=admin_user):

        # ACT
        response = admin_client.get(
            "/admin-protected",
            headers={"Authorization": "Bearer any-valid-token"}
        )
        data = response.get_json()

    # Assert
    assert response.status_code == 200
    assert data["message"] == "admin access granted"


def test_require_admin_with_non_admin_role_fails(admin_client):
    """
    GIVEN a user WIHTOUT the "admin" role
    WHEN they access a route protected by @require_admin
    THEN the request should be forbidden (403)
    """
    # Arrange
    test_user = {
        "_id": ObjectId(),
        "email": "test_user@example.com",
        "role": "user" # CRUCIAL
        }
    # Patch the dependencies of the inner decorator (@require_jwt)
    with patch("app.utils.decorators.jwt.decode", return_value={"sub": str(test_user["_id"])}), \
        patch("app.utils.decorators.mongo.db.users.find_one", return_value=test_user):

        response = admin_client.get(
            "/admin-protected",
            headers={"Authorization": "Bearer any-valid-token"}
        )
        data = response.get_json()

    # Assert:
    # Check for a 403 Forbidden status and the correct error message from abort().
    assert response.status_code == 403
    assert data["error"] == "Admin privileges required."


def test_require_admin_fails_if_jwt_is_invalid(admin_client):
    """
    GIVEN a request without a valid token
    WHEN they access a route protected by @require_admin
    THEN the inner @require_jwt decorator should reject it first (401)
    """
    # Arrange: No mocking is needed. We are testing the real failure case.

    # Act: Make a request with no Authorization header.
    response = admin_client.get("/admin-protected")

    # Assert: We expect a 401 error from the @require_jwt decorator.
    assert response.status_code == 401
