# pylint: disable=too-few-public-methods

"""
The central, organized place for  the application's settings.

Loads environment variables (and other sensitive values) from a .env file and
Defines the Config class to be used.

"""

import os

from dotenv import load_dotenv

# Find the absolute path of the root directory of the project
basedir = os.path.abspath(os.path.dirname(__file__))
# Build the path to the .env file located in the parent directory of the project root
dotenv_path = os.path.join(os.path.dirname(basedir), ".env")
# Load environment variables to be used
load_dotenv(dotenv_path=dotenv_path)


class Config:
    """Set Flask configuration variables from environment variables"""

    # General config
    SECRET_KEY = os.environ.get("SECRET_KEY")
    FLASK_APP = os.environ.get("FLASK_APP")
    FLASK_ENV = os.environ.get("FLASK")  # values will be 'development' or 'production'
    API_KEY = os.environ.get("API_KEY")

    # Database config
    MONGO_URI = os.environ.get("MONGO_CONNECTION")
    DB_NAME = os.environ.get("PROJECT_DATABASE")
    COLLECTION_NAME = os.environ.get("PROJECT_COLLECTION")
