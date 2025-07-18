"""Initialize the Flask app and register all routes."""

import os
from flask import Flask
from app.config import Config

def create_app(test_config=None):
    """Application factory pattern."""

    app = Flask(__name__)

    # 1. Load the default configuration from the Config object.
    app.config.from_object(Config)

    if test_config: # Override with test specifics
        app.config.from_mapping(test_config)

    # Import routes
    from app.routes import \
        register_routes  # pylint: disable=import-outside-toplevel

    register_routes(app)

    return app
