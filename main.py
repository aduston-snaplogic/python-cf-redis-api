"""
python-cf-redis-api provides a simple RESTful front-end for interacting with Redis instances.
It is designed to run locally as well as be deployed in CloudFoundry.

Author: Adam Duston
License: MIT
"""
import os
import sys
import redis
import json
from flask import Flask, jsonify, abort
from flask import __version__ as flask_version

app = Flask(__name__)

test_values = {'food': 'cheese', 'drink': 'coffee', 'animal': 'capybara', '1': 'two'}

# Config file should be provided to specify runtime values if not running in CF.
# If no config is set the app should log an error and fail.
# Checks for VCAP_APPLICATION as an indicator of a CloudFoundry environment, and loads
# the config file only if CF is not detected.
CONFIG_FILE = "./config/config.json"
config = ""
if not os.getenv("VCAP_APPLICATION"):
    try:
        app.logger.info("CF environment not found. Trying config file.")
        with open(CONFIG_FILE, 'r') as config_file:
            config = json.load(config_file)

    except IOError:
        app.logger.error("Could not open config file {0} - Quitting.".format(CONFIG_FILE))
        sys.exit(1)

    except ValueError:
        app.logger.error("Could not load config file. Does not contain valid JSON data.")
        sys.exit(1)

# Look for redis instances in the CF
redis_instances = list()
vcap_services = os.getenv("VCAP_SERVICES")
if vcap_services:
    services = json.loads(vcap_services)
    for k in services.keys():
        for i in services[k]:
            if 'redis' in i['tags']:
                redis_instances.append(i)
elif config:
    redis_instances = config['redis']
else:
    redis_instances = list()


@app.route('/')
def main():
    """ The 'main' route / will just report some basic environment information for now. """
    python_version = sys.version
    newline = "<br/>"
    redis_info = ""
    for i in redis_instances:
        redis_info += "{0}:{1}{2}".format(i['credentials']['host'], i['credentials']['port'], newline)

    return "python-cf-redis-api started successfully." \
           "{2}{2}Python: {0}{2}" \
           "Flask: {1}" \
           "{2}{2}" \
           "Redis instances:{2}" \
           "{3}".format(python_version, flask_version, newline, redis_info)


@app.route('/api/keys/<string:key_value>', methods=['GET'])
def get_value(key_value):
    """ GET to the route keys/$key will return the value associated with that key."""
    try:
        value = test_values[key_value]
    except KeyError:
        abort(404)

    return jsonify({'value': value})

if __name__ == '__main__':
    """ Setup the app environment and start the Flask application. """

    # CF provides the bind port via an environment variable. Default to 9099 if one isn't found there.
    BIND_PORT = os.getenv("VCAP_APP_PORT")

    if BIND_PORT:
        # Run the app, listening on all IPs with our chosen port number
        app.run(host='0.0.0.0', port=int(BIND_PORT))
    else:
        try:
            app.run(host='0.0.0.0', port=int(config['port']))

        except ValueError:
            app.logger.error("{0} is not a valid port number. Port must be an integer.".format(config['port']))
            sys.exit(1)
