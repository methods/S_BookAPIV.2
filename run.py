"""Entry point for running the Flask application.

This script imports the Flask application factory from the app package,
creates an instance of the application, and runs it in debug mode.
"""
from app import create_app

app = create_app()
