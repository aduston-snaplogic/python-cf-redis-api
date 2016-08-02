"""
python-cf-redis-api provides a simple RESTful front-end for interacting with Redis instances.
It is designed to run locally as well as be deployed in CloudFoundry.

Author: Adam Duston
License: MIT
"""
import os
import sys
import flask


app = flask.Flask(__name__)

# CF provides the bind port via an environment variable. Default to 9099 if one isn't found there.
port = int(os.getenv("VCAP_APP_PORT", '9099'))


@app.route('/')
def main():
    """ The 'main' route / will just report some basic environment information for now. """
    flask_version = flask.__version__
    python_version = sys.version
    newline = "<br/>"
    return "python-cf-redis-api started successfully.{2}{2}Python: {0}{2}Flask: {1}".format(python_version,
                                                                                            flask_version,
                                                                                            newline)

if __name__ == '__main__':
    # Run the app, listening on all IPs with our chosen port number
    app.run(host='0.0.0.0', port=port)
