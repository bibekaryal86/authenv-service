import os

from fastapi import FastAPI
from pymongo import MongoClient

# Constants
APP_ENV = 'APP_ENV'
SECRET_KEY = 'SECRET_KEY'
MONGODB_USR_NAME = 'MONGODB_USR_NAME'
MONGODB_USR_PWD = 'MONGODB_USR_PWD'
BASIC_AUTH_USR = 'BASIC_AUTH_USR'
BASIC_AUTH_PWD = 'BASIC_AUTH_PWD'


# utility Functions
def is_production():
    return os.getenv(APP_ENV) == 'production'


def validate_input():
    missing_variables = []

    if os.getenv(APP_ENV) is None:
        missing_variables.append(APP_ENV)

    if os.getenv(SECRET_KEY) is None:
        missing_variables.append(SECRET_KEY)

    if os.getenv(MONGODB_USR_NAME) is None:
        missing_variables.append(MONGODB_USR_NAME)

    if os.getenv(MONGODB_USR_PWD) is None:
        missing_variables.append(MONGODB_USR_PWD)

    if os.getenv(BASIC_AUTH_USR) is None:
        missing_variables.append(BASIC_AUTH_USR)

    if os.getenv(BASIC_AUTH_PWD) is None:
        missing_variables.append(BASIC_AUTH_PWD)

    if len(missing_variables) != 0:
        raise ValueError('The following env variables are missing: {}'.format(missing_variables))


def startup_db_client(app: FastAPI):
    app.mongo_client = __get_mongo_client()
    print('Connected to MongoDb Client!')


def shutdown_db_client(app: FastAPI):
    app.mongo_client.close()
    print('Disconnected from MongoDb Client!')


def __get_mongo_client():
    user_name = os.getenv(MONGODB_USR_NAME)
    password = os.getenv(MONGODB_USR_PWD)
    connection_string = 'mongodb+srv://{}:{}@appdetails.bulegrc.mongodb.net/?retryWrites=true&w=majority' \
        .format(user_name, password)
    return MongoClient(connection_string)
