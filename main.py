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
from flask import Flask, jsonify, abort, request
from flask import __version__ as flask_version

app = Flask(__name__)

# A test values file, if provided, will pre-load the given key/value pairs into all redis instances.
TEST_VALUES_FILE = './config/test_values.json'

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
redis_instances = dict()
vcap_services = os.getenv("VCAP_SERVICES")
if vcap_services:
    services = json.loads(vcap_services)
    for k in services.keys():
        for i in services[k]:
            if 'redis' in i['tags']:
                redis_instances[i['name']] = i['credentials']
elif config:
    for i in config['redis']:
        redis_instances[i['name']] = i['credentials']
else:
    # Just use an empty dict if redis instances can't be located from any source.
    redis_instances = dict()


# Create a client for each redis instance. Try to verify if the connection is good or not.
redis_clients = dict()
for name in redis_instances.keys():
    r = redis_instances[name]
    try:
        redis_client = redis.StrictRedis(socket_timeout=10, host=r['host'], port=r['port'], password=r['password'])
        if redis_client.ping():
            redis_clients[name] = redis_client
            redis_instances[name]['connection_status'] = "Good"
    except redis.ConnectionError, e:
        # Failed to connect to redis instance.
        app.logger.error("Failed to connect to redis at {0}:{1}: {2}".format(r['host'], r['port'], e.message))
        redis_instances[name]['connection_status'] = e.message
        redis_clients[name] = None
    except redis.ResponseError, e:
        if e.message == 'invalid password':
            app.logger.error("Password invalid for {0}:{1}".format(r['host'], r['port']))
            redis_instances[name]['connection_status'] = "Invalid Password"
            redis_clients[name] = None

# Grab a single redis instance to use by default. Default to None.
default_redis = None
if len(redis_instances) > 0:
    name = redis_instances.keys().pop()
    default_redis = redis_instances[name]
    default_redis['name'] = name

# If the user has provided a test values json file, load the values into the redis instances at start-up.
if os.path.isfile(TEST_VALUES_FILE):
    with open(TEST_VALUES_FILE) as f:
        test_values = json.load(f)

    if len(test_values) > 0:
        for name in redis_instances.keys():
            if redis_instances[name]['connection_status'] == "Good":
                client = redis_clients[name]
                client.mset(test_values)


@app.route('/')
def main():
    """ The 'main' route / will just report some basic environment information for now. """
    python_version = sys.version
    newline = "<br/>"
    redis_info = ""
    default_redis_info = ""

    for name in redis_instances.keys():
        r = redis_instances[name]
        font_color = "red"
        if r['connection_status'] == "Good":
            font_color = "green"

        redis_info += "<font color={0}>{1}: {2}:{3} - {4}</font>{5}".format(font_color, name, r['host'], r['port'],
                                                                            r['connection_status'], newline)

    if default_redis:
        font_color = "red"
        if default_redis['connection_status'] == "Good":
            font_color = "green"

        default_redis_info = "<font color={0}>{1}: {2}:{3} - {4}</font>{5}".format(font_color, default_redis['name'],
                                                                                   default_redis['host'],
                                                                                   default_redis['port'],
                                                                                   default_redis['connection_status'],
                                                                                   newline)

    output = "python-cf-redis-api started successfully. \
             {2}{2}Python: {0}{2} \
             Flask: {1} \
             {2}{2} \
             Redis instances:{2} \
             {3}".format(python_version, flask_version, newline, redis_info)

    if default_redis:
        output += "{1}Default Redis Instance:{1}{0}".format(default_redis_info, newline)

    return output


@app.route('/api/redis_instances', methods=['GET'])
def get_redis_instances():
    """ Provide a route for getting info about the redis instances in the environment. """
    if redis_instances:
        return jsonify(redis_instances)
    else:
        abort(404)


@app.route('/api/key/<string:key>', methods=['GET'])
def get_value(key):
    """ GET to the route keys/$key will return the value associated with that key."""
    redis_name = request.args.get('redis_instance', None)
    value = None
    if redis_name:
        try:
            r = redis_clients[redis_name]
        except KeyError:
            # Return a 400 if they specified a redis instance that the app doesn't know about.
            app.logger.error("Requested Redis instance {0} does is unknown".format(redis_name))
            abort(400)
    else:
        r = redis_clients[default_redis['name']]

    if r:
        # Get the value for the key from redis. If a value doesn't exist for this key return a 404 error.
        value = r.get(key)
        if not value:
            abort(404)
    else:
        abort(500)

    return jsonify({'value': value})


@app.route('/api/key/<string:key>', methods=['PUT', 'POST'])
def set_value(key):
    """ Route to create or update a key/value pair in redis """
    redis_name = request.args.get('redis_instance', None)
    if redis_name:
        try:
            r = redis_clients[redis_name]
        except KeyError:
            # Return a 400 if they specified a redis instance that the app doesn't know about.
            app.logger.error("Requested Redis instance {0} is unknown".format(redis_name))
            abort(400)
    else:
        r = redis_clients[default_redis['name']]

    if not request.json:
        abort(400)
    if 'value' not in request.json:
        abort(400)

    value = request.json.get('value')
    result = r.set(key, value)
    if result:
        return jsonify({'result': result})
    else:
        app.logger.error("An error occurred updating redis.")
        abort(500)


@app.route('/api/key/<string:key>', methods=['DELETE'])
def delete_key(key):
    """ Delete the given key from redis """
    redis_name = request.args.get('redis_instance', None)
    if redis_name:
        try:
            r = redis_clients[redis_name]
        except KeyError:
            # Return a 400 if they specified a redis instance that the app doesn't know about.
            app.logger.error("Requested Redis instance {0} is unknown".format(redis_name))
            abort(400)
    else:
        r = redis_clients[default_redis['name']]

    result = r.delete(key)
    return jsonify({'result': result})

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
