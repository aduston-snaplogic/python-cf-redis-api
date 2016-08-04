# Python Testing API for Redis and CloudFoundry

This simple [Flask](http://flask.pocoo.org/) based Python application provides 
a simple RESTful API for interacting with Redis instances. It is designed to run 
either in CloudFoundry, but also supports running locally or in a non-CF environment.

The API allows you to get, set, and delete Redis key/value pairs. 
 
### Getting Started

#### Deploying to CloudFoundry

To quickly deploy this app into CloudFoundry:
    
    git clone https://github.com/compybara/python-cf-redis-api.git
    cd python-cf-redis-api
    cf push 
    
At start-up the application will attempt to determine if it is running in CloudFoundry, and 
detect any instances of Redis in its `VCAP_SERVICES` environment variable. 

It will then attempt to connect to the Redis instances. The root page of the app will display
some status information, including the Redis instances it is aware of and whether it was able
to successfully communicate with them at start-up. 

#### Running Outside of CloudFoundry

To the run the application on a system outside of CloudFoundry you need to make sure that
your Python environment is set up with the correct dependencies, and that the `config.json`
file is configured correctly (See the Setup section below for details). 

To setup the app with [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/):

    git clone https://github.com/compybara/python-cf-redis-api.git
    cd python-cf-redis-api
    virtualenv venv
    source venvv/bin/activate
    pip install -r requirements.txt
    
To start the app:
    
    python main.py
    

#### Setup 

The `config/` directory contains a couple of files that the app will read at start-up 
and will allow you to specify some initial setup parameters for the app.  

`config.json` 

This file allows configuring the app for running locally. This file is only loaded
if the app determines that it is not running in CloudFoundry. It can be used to configure
the bind port for the application as well as the Redis instances it should use. The 
structure of the `redis` section of the config is designed to mirror the structure of the
service variable in CloudFoundry. A sample config file is included in `./config_sample/config.json`. 

`test_values.json`

The app will look for this file at start-up, and if it exists it will load the key-value pairs
from it into each Redis instance it can connect to. This makes it easy to provide some test values without
setting them manually. 

#### Usage

The API exposes the following endpoints. 

#### GET /api/redis_instances

Returns the configuration details for the Redis instances in the environment. 

    $ curl -H "Content-Type: application/json" -X GET https://localhost:9099/api/redis_instances
    {
      "redis-test-1": {
        "connection_status": "Good",
        "host": "10.72.6.32",
        "name": "redis-test-1",
        "password": "01991efc-5a67-11e6-8b77-86f30ca893d3",
        "port": 50415
      },
      "redis-test-2": {
        "connection_status": "Good",
        "host": "10.72.6.32",
        "password": "f7824628-5a66-11e6-8b77-86f30ca893d3",
        "port": 33017
      }
    }

#### GET /api/key/:key

Get the value of a key. Returns `404` if the key does not exist. 

    $ curl -H "Content-Type: application/json" -X GET https://localhost:9099/api/key/test
    {
      "value": "hello world"
    }

#### PUT /api/key/:key

Set the value of a key in Redis. The value of the key needs to be provided in the 'value'
field in the of the request data. Will return `"result": true` if the update was successful.
    
    $ curl -H "Content-Type: application/json" -X PUT -d '{"value": "Hooray for kittens."}' https://localhost:9099/api/key/test
    {
      "result": true
    }
    
A `500` error code is returned if there was some issue updating Redis.

#### POST /api/key/:key

Same as `PUT`

#### DELETE /api/key/:key

Deletes the key in Redis. Returns `1` if the key was found and deleted, and `0` if the key did not exist.

    $ curl -H "Content-Type: application/json" -X DELETE https://localhost:9099/api/key/test
    {
      "result": 1
    }
<!-- Break up the code blocks-->
    $ curl -H "Content-Type: application/json" -X GET https://localhost:9099/api/key/test?redis_instance=python-redis-test-1
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
    <title>404 Not Found</title>
    <h1>Not Found</h1>
    <p>The requested URL was not found on the server.  If you entered the URL manually please check your spelling and try again.</p>
<!-- Break up the code blocks-->
    $ curl -H "Content-Type: application/json" -X DELETE https://python-cf-redis-api.run.aws-usw02-pr.ice.predix.io/api/key/test
    {
      "result": 0
    }

#### Specifying the Redis Instance

The `/api/key/:key` endpoints support specifying which instance of redis to communicate with. 

This is done with the url parameter `redis_instance=` and the name of the instance. You can find the
name for each instance of Redis with the `/api/redis_instances` endpoint. 

Example:

    $ curl -H "Content-Type: application/json" -X PUT -d '{"value": "Tabs are better."}' https://localhost:9099/api/key/test?redis_instance=redis-test-1
    {
      "result": true
    }
    $ curl -H "Content-Type: application/json" -X PUT -d '{"value": "Spaces are better."}' https://localhost:9099/api/key/test?redis_instance=redis-test-2
    {
      "result": true
    }
<!-- Break up the code blocks-->
    $ curl -H "Content-Type: application/json" -X GET https://localhost:9099/api/key/test?redis_instance=redis-test-1
    {
      "value": "Tabs are better."
    }
    $ curl -H "Content-Type: application/json" -X GET https://localhost:9099/api/key/test?redis_instance=python-redis-test-2
    {
      "value": "Spaces are better."
    }