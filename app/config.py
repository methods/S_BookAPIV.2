# pylint: disable=too-few-public-methods

"""
Application configuration module for Flask.

Loads environment variables from a .env file and defines the Config class
used to configure Flask and database connection settings.
"""

import os
from dotenv import load_dotenv

# Find the absolute path of the root directory of the project
basedir = os.path.abspath(os.path.dirname(__file__))
# Load environment variables to be used
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """ Set Flask configuration variables from environment variables"""

    # General config
    SECRET_KEY = os.environ.get('SECRET_KEY')
    FLASK_APP = os.environ.get('FLASK_APP')
    FLASK_ENV = os.environ.get('FLASK') # values will be 'development' or 'production'

    # Database config
    MONGO_URI = os.environ.get("MONGO_CONNECTION")
    DB_NAME = os.environ.get("PROJECT_DATABASE")
    COLLECTION_NAME = os.environ.get("PROJECT_COLLECTION")
