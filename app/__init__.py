"""Initialize the Flask app and register all routes."""

import os
from flask import Flask
from app.config import Config

def create_app(test_config=None):
    """Application factory pattern."""

    app = Flask(__name__)

    if test_config is None:
        # Load configuration from our Config object
        app.config.from_object(Config)
    else:
        # Load the test configuration passed in
        app.config.from_mapping(test_config)

    # Import routes — routes can import app safely because it exists
    from app.routes import \
        register_routes  # pylint: disable=import-outside-toplevel

    register_routes(app)

    return app
