"""Module for Flask extensions."""

from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt

# Createempty PyMongo extension object globally
# This way, we can import it in other files and avoid a code smell: tighly-coupled, cyclic error
mongo = PyMongo()
bcrypt = Bcrypt()
