"""
services.py - Define tools for discovering and connecting to Redis services.
"""
from cfenv import AppEnv
import os
import sys
import redis

from flask import Flask

app = Flask(__name__)
redis_instances = dict()


class RedisService:
    """ Class to describe a Redis service instance """

    _client = None
    _connection_status = None

    def __init__(self, host, port=6379, password=""):
        """ Constructor for the RediService takes the credentials as keyword args. """
        self._host = host
        self.port = port
        self._password = password

    @property
    def host(self):
        """ The IP address or URI to the Redis service instance host. """
        return self._host

    @property
    def port(self):
        """ The port used by the Redis service. """
        return self._port

    @port.setter
    def port(self, value):
        """ Ensure the port converts to an integer. """
        try:
            self._port = int(value)
        except ValueError, e:
            app.logger.error("Could not convert port value {} to an integer.".format(value))
            raise e

    @property
    def password(self):
        """ The Password to use for logging into Redis """
        return self._password


    @property
    def client(self):
        """ Returns the Redis service client """
        if not self._client:
            self._client = self.get_client()

        return self._client

    @property
    def connection_status(self):
        """ Check whether the redis connection status is good. Returns a status string. """
        return self._connection_status

    def get_client(self):
        """ Create a connection to the Redis Service """
        try:
            client = redis.StrictRedis(socket_timeout=10, host=self._host, port=self._port, password=self._password)
            if client.ping():
                self._client = client
                self._connection_status = "Good"
        except redis.ConnectionError, e:
            app.logger.error("Failed to connect to redis at {0}:{1}: {2}".format(self._host, self._port, e.message))
            self._connection_status = e.message
            self._client = None
        except redis.ResponseError, e:
            if e.message == 'invalid password':
                app.logger.error("Password invalid for {0}:{1}".format(self._host, self._port))
                self._connection_status = "Invalid Password"
                self._client = None


def discover_services(config):
    """ Create the dict of redis_instances. If they can't be parsed from the CF environemnt use the config file. """
    env = AppEnv()
    if env.app:
        # App is running in CloudFoundry
        services = env.services
        for s in services:
            if 'redis' in s.env['tags']:
                redis_instances[s.name] = RedisService(**s.credentials)

    else:
        app.logger.info("CF environment not found. Trying config file.")
        if config:
            try:
                for r in config['redis']:
                    redis_instances[r['name']] = RedisService(**r['credentials'])
            except KeyError:
                app.logger.error("No Redis instances loaded from config file. Cannot discover any services.")
        else:
            app.logger.error("No config loaded. Cannot discover any services.")

    # If there are any services configured pick a default at random.
    if redis_instances:
        redis_instances['default'] = redis_instances[redis_instances.keys().pop()]



