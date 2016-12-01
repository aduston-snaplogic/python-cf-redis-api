"""
python-cf-redis-api provides a simple RESTful front-end for interacting with Redis in CloudFoundry

Author: Adam Duston
License: MIT
"""
from flask import Flask

# Initialize the Flask app
app = Flask(__name__)

# Import the routes and services modules
from app import services
from app import routes