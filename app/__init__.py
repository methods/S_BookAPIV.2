"""Initialize the Flask app and register all routes."""

import os

from flask import Flask
from flask_pymongo import PyMongo

from app.config import Config

# Create PyMongo extension object outside the factory
# in the global scope, creating an "empty" extension object
# This way, we can import it in other files
mongo = PyMongo()


def create_app(test_config=None):
    """Application factory pattern."""

    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:  # Override with test specifics
        app.config.from_mapping(test_config)

    # Connect Pymongo to our specific app instance
    mongo.init_app(app)

    # Import blueprints inside the factory
    from app.routes.legacy_routes import register_legacy_routes # pylint: disable=import-outside-toplevel
    from app.routes.auth_routes import auth_bp # pylint: disable=import-outside-toplevel

    # Register routes with app instance
    register_legacy_routes(app)
    app.register_blueprint(auth_bp)

    return app
