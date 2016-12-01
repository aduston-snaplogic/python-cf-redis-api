"""
python-cf-redis-api provides a simple RESTful front-end for interacting with Redis instances.
It is designed to run locally as well as be deployed in CloudFoundry.

Author: Adam Duston
License: MIT
"""
import sys
import json
from flask import Flask
from cfenv import AppEnv
from logging import StreamHandler, DEBUG, INFO
from app import app, services

# Specify a default config file to attempt to load to get some config details. If no file can be loaded just ignore
# them in most cases. If necessary values can't be loaded from CF or the config the app will faile.
CONFIG_FILE = "./config/config.json"

if __name__ == '__main__':
    """ Setup the app environment and start the Flask application. """
    env = AppEnv()

    # Set up logging.
    handler = StreamHandler(sys.stdout)
    handler.setLevel(INFO)


    # Try to load the config from the file.
    config = None
    try:
        with open(CONFIG_FILE, 'r') as config_file:
            config = json.load(config_file)

    except IOError:
        app.logger.error("Could not open config file.".format(CONFIG_FILE))

    except ValueError:
        app.logger.error("Could not load config file. Does not contain valid JSON data.")

    # If a config was provided and loaded try to set up some values from it.
    config_port = None
    if config:
        try:
            # Turn on debug logging if specified.
            if config['debug'] == True:
                handler.setLevel(DEBUG)
                app.debug = DEBUG
        except KeyError:
            app.logger.info("Debug logging not enabled.")


        try:
            config_port = int(config['port'])

        except KeyError:
            app.logger.info("No port specified in config file. ")
        except TypeError:
            app.logger.error("Port specified in config file must be an Integer.")

    app.logger.addHandler(handler)

    services.discover_services(config)
    if env.port:
        app.run(host='0.0.0.0', port=env.port)
    elif config_port:
        app.run(host='0.0.0.0', port=config_port)
    else:
        app.logger.error("No port specified in config, and none availble from CloudFoundry. Quitting.")
        sys.exit(1)