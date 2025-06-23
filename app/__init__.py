"""Initialize the Flask app and register all routes."""

import os
from dotenv import load_dotenv
from flask import Flask

def create_app():
    """Application factory pattern."""
    # Load the env variables to use here
    load_dotenv()

    app = Flask(__name__)
    # Use app.config to set config connection details
    app.config['MONGO_URI'] = os.getenv('MONGO_CONNECTION')
    app.config['DB_NAME'] = os.getenv('PROJECT_DATABASE')
    app.config['COLLECTION_NAME'] = os.getenv('PROJECT_COLLECTION')

    # Import routes — routes can import app safely because it exists
    from app.routes import register_routes # pylint: disable=import-outside-toplevel
    register_routes(app)

    return app
