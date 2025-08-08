"""Module for Flask extensions."""

from flask_pymongo import PyMongo


# Create empty PyMongo extension object globally
# This way, we can import it in other files and avoid a code smell: tightly-coupled, cyclic error
mongo = PyMongo()
