import os
from dotenv import load_dotenv
from flask import Flask

app = Flask(__name__)

# Use app.config to set config connection details
load_dotenv()
app.config['MONGO_URI'] = os.getenv('MONGO_CONNECTION')
app.config['DB_NAME'] = os.getenv('PROJECT_DATABASE')
app.config['COLLECTION_NAME'] = os.getenv('PROJECT_COLLECTION')

# Import routes — routes can import app safely because it exists
from app.routes import register_routes
register_routes(app)

# Expose `app` for importing
__all__ = ["app"]
