"""
routes.py - Define views / api routes for the app.
"""
from os import uname
from sys import version
from app import app, services
from flask import __version__ as flask_version
from flask import render_template, jsonify, abort, request

@app.route('/')
@app.route('/index')
def index():
    """ The 'index' route / will just report some basic environment information for now. """
    template_vars = dict()

    template_vars['title'] = "Redis Example App for Python"
    template_vars['python_version'] = version
    template_vars['os_info'] = "{0} {1} {2}".format(uname()[0], uname()[2], uname()[4])
    template_vars['flask_version'] = flask_version

    return render_template('index.html', redis_instances=services.redis_instances, **template_vars)

@app.route('/api/redis_instances', methods=['GET'])
def redis_instances():
    output_dict = dict()
    if len(services.redis_instances.keys()) > 0:
        for name, redis in services.redis_instances.iteritems():
            app.logger.debug("{0}: {1}".format(name, redis.__dict__))
            output_dict[name] = redis.to_dict()
        return jsonify(output_dict)
    else:
        return jsonify({})

@app.route('/api/key/<string:key>', methods=['GET'])
def get_value(key):
    """ GET to the route keys/$key will return the value associated with that key."""
    redis_name = request.args.get('redis_instance', None)
    value = None
    r = None
    if redis_name:
        try:
            r = services.redis_instances[redis_name]
        except KeyError:
            # Return a 400 if they specified a redis instance that the app doesn't know about.
            app.logger.error("Requested Redis instance {0} does is unknown".format(redis_name))
            abort(400, "{} is not a known Redis service.".format(redis_name))
    else:
        try:
            r = services.redis_instances['default']
        except KeyError:
            abort(502, "No Redis services available.")

    if r:
        # Get the client and verify the connection status.
        client = r.client
        if r.connection_status != "Good":
            abort(502, r.connection_status)

        # Get the value for the key from redis. If a value doesn't exist for this key return a 404 error.
        value = client.get(key)
        if not value:
            abort(404, "Key {} not found.".format(key))
    else:
        abort(502, "Could not connect to any Redis Service.")

    return jsonify({'value': value})

@app.route('/api/key/<string:key>', methods=['PUT', 'POST'])
def set_value(key):
    """ Route to create or update a key/value pair in redis """
    redis_name = request.args.get('redis_instance', None)
    r = None

    if redis_name:
        try:
            r = services.redis_instances[redis_name]
        except KeyError:
            # Return a 400 if they specified a redis instance that the app doesn't know about.
            app.logger.error("Requested Redis instance {0} is unknown".format(redis_name))
            abort(400, "{} is not a known Redis service.".format(redis_name))
    else:
        try:
            r = services.redis_instances['default']
        except KeyError:
            abort(502, "No Redis services available.")

    if not request.json:
        abort(400, "No data provided.")

    if 'value' not in request.json:
        abort(400, "Must provide data for 'value' in request body.")

    if r:
        client = r.client
        if r.connection_status != "Good":
            abort(502, r.connection_status)

        value = request.json.get('value')
        result = client.set(key, value)
        if result:
            return jsonify({'result': result})
        else:
            app.logger.error("An error occurred updating Redis.")
            abort(502, "An error occurred updating Redis")
    else:
        abort(502, "Could not connect to any Redis Service.")


@app.route('/api/key/<string:key>', methods=['DELETE'])
def delete_key(key):
    """ Delete the given key from redis """
    redis_name = request.args.get('redis_instance', None)
    r = None

    if redis_name:
        try:
            r = services.redis_instances[redis_name]
        except KeyError:
            # Return a 400 if they specified a redis instance that the app doesn't know about.
            app.logger.error("Requested Redis instance {0} is unknown".format(redis_name))
            abort(400, "{} is not a known Redis service.".format(redis_name))
    else:
        try:
            r = services.redis_instances['default']
        except KeyError:
            abort(502, "No Redis services available.")

    if r:
        client = r.client
        if r.connection_status != "Good":
            abort(502, r.connection_status)

        result = client.delete(key)
        return jsonify({'result': result})
    else:
        abort(502, "Could not connect to any Redis Service.")


@app.errorhandler(400)
def error_400(message):
    return message


@app.errorhandler(502)
def error_502(message):
    return message