import http
import os
import secrets
from datetime import datetime, timedelta
from http import HTTPStatus

import jwt
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.security import HTTPBasic, HTTPBearer, HTTPBasicCredentials, HTTPAuthorizationCredentials
from jwt import PyJWTError
from pymongo import MongoClient

# Constants
APP_ENV = 'APP_ENV'
SECRET_KEY = 'SECRET_KEY'
MONGODB_USR_NAME = 'MONGODB_USR_NAME'
MONGODB_USR_PWD = 'MONGODB_USR_PWD'
BASIC_AUTH_USR = 'BASIC_AUTH_USR'
BASIC_AUTH_PWD = 'BASIC_AUTH_PWD'


# utility functions
def is_production():
    return os.getenv(APP_ENV) == 'production'


# startup
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


# security
http_basic_security = HTTPBasic()  # for main, env_props module
http_bearer_security = HTTPBearer()  # for users module


def validate_http_basic_credentials(http_basic_credentials: HTTPBasicCredentials):
    valid_username = os.getenv(BASIC_AUTH_USR)
    valid_password = os.getenv(BASIC_AUTH_PWD)
    input_username = http_basic_credentials.username
    input_password = http_basic_credentials.password
    is_correct_username = secrets.compare_digest(valid_username.encode('utf-8'), input_username.encode('utf-8'))
    is_correct_password = secrets.compare_digest(valid_password.encode('utf-8'), input_password.encode('utf-8'))
    if not (is_correct_username and is_correct_password):
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail='Invalid Credentials!')


def encode_http_auth_credentials(username, source_ip):
    token_claim = {
        'username': username,
        'source_ip': source_ip,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload=token_claim, key=os.getenv(SECRET_KEY), algorithm='HS256')


def validate_http_auth_credentials(http_auth_credentials: HTTPAuthorizationCredentials, username: str):
    try:
        token_claims = jwt.decode(jwt=http_auth_credentials.credentials, key=os.getenv(SECRET_KEY),
                                  algorithms=['HS256'])
        token_username = token_claims.get('username')

        if token_username == username:
            return token_username

        raise HTTPException(status_code=http.HTTPStatus.UNAUTHORIZED,
                            detail={'msg': 'Invalid Credentials!', 'errMsg': 'Invalid Credentials!'})
    except PyJWTError as ex:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail={'msg': 'Invalid Credentials!', 'errMsg': str(ex)})
