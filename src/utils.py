import http
import sched
import secrets
import time
from datetime import datetime, timedelta
from pydantic_settings import BaseSettings, SettingsConfigDict
import jwt
from functools import lru_cache
from fastapi import FastAPI, Request
from fastapi import HTTPException
from fastapi.security import HTTPBasic, HTTPBearer, HTTPBasicCredentials, HTTPAuthorizationCredentials
from jwt import PyJWTError
from pymongo import MongoClient

# Constants
SERVICE_AUTH_USR = '-usr'
SERVICE_AUTH_PWD = '-pwd'
GATEWAY_AUTH_EXCLUSIONS = 'authExclusions'
GATEWAY_AUTH_CONFIGS = 'authConfigs'
GATEWAY_ROUTE_PATHS = 'routePaths'
GATEWAY_BASE_URLS = 'baseUrls_{}'
# https://github.com/bibekaryal86/pets-gateway-simple/blob/main/app/src/main/java/pets/gateway/app/util/Util.java#L42
RESTRICTED_HEADERS = ['accept-charset',
                      'accept-encoding',
                      'access-control-request-headers',
                      'access-control-request-method',
                      'connection',
                      'content-length',
                      'cookie',
                      'cookie2',
                      'content-transfer-encoding',
                      'date',
                      'expect',
                      'host',
                      'keep-alive',
                      'origin',
                      'referer',
                      'te',
                      'trailer',
                      'transfer-encoding',
                      'upgrade',
                      'user-agent',
                      'via',
                      'authorization'  # auth is set separately using auth parameter
                      ]


# ENVIRONMENT VARIABLES
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")


@lru_cache()
def get_settings():
    return Settings()


APP_ENV = get_settings().app_env
SECRET_KEY = get_settings().secret_key
MONGODB_USR_NAME = get_settings().mongodb_usr_name
MONGODB_USR_PWD = get_settings().mongodb_usr_pwd
BASIC_AUTH_USR = get_settings().basic_auth_usr
BASIC_AUTH_PWD = get_settings().basic_auth_pwd


# startup
def validate_input():
    missing_variables = []

    if APP_ENV is None:
        missing_variables.append('APP_ENV')

    if SECRET_KEY is None:
        missing_variables.append('SECRET_KEY')

    if MONGODB_USR_NAME is None:
        missing_variables.append('MONGODB_USR_NAME')

    if MONGODB_USR_PWD is None:
        missing_variables.append('MONGODB_USR_PWD')

    if BASIC_AUTH_USR is None:
        missing_variables.append('BASIC_AUTH_USR')

    if BASIC_AUTH_PWD is None:
        missing_variables.append('BASIC_AUTH_PWD')

    if len(missing_variables) != 0:
        raise ValueError('The following env variables are missing: {}'.format(missing_variables))


def startup_db_client(app: FastAPI):
    app.mongo_client = __get_mongo_client()
    print('Connected to MongoDb Client!')


def shutdown_db_client(app: FastAPI):
    app.mongo_client.close()
    print('Disconnected from MongoDb Client!')


def __get_mongo_client():
    connection_string = 'mongodb+srv://{}:{}@appdetails.bulegrc.mongodb.net/?retryWrites=true&w=majority' \
        .format(MONGODB_USR_NAME, MONGODB_USR_PWD)
    return MongoClient(connection_string)


# security
http_basic_security = HTTPBasic()  # for main, env_props module
http_bearer_security = HTTPBearer()  # for users module


def validate_http_basic_credentials(request: Request, http_basic_credentials: HTTPBasicCredentials):
    valid_username = BASIC_AUTH_USR
    valid_password = BASIC_AUTH_PWD
    input_username = http_basic_credentials.username
    input_password = http_basic_credentials.password
    is_correct_username = secrets.compare_digest(valid_username.encode('utf-8'), input_username.encode('utf-8'))
    is_correct_password = secrets.compare_digest(valid_password.encode('utf-8'), input_password.encode('utf-8'))
    if not (is_correct_username and is_correct_password):
        raise_http_exception(request=request, status_code=http.HTTPStatus.UNAUTHORIZED, msg='Invalid Credentials',
                             err_msg='Basic Credentials')


def encode_http_auth_credentials(username, source_ip):
    token_claim = {
        'username': username,
        'source_ip': source_ip,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload=token_claim, key=SECRET_KEY, algorithm='HS256')


def validate_http_auth_credentials(request: Request, http_auth_credentials: HTTPAuthorizationCredentials,
                                   username: str = None):
    try:
        token_claims = jwt.decode(jwt=http_auth_credentials.credentials, key=SECRET_KEY,
                                  algorithms=['HS256'])
        token_username = token_claims.get('username')

        if username is None:
            return token_username
        elif username == token_username:
            return token_username

        raise_http_exception(request=request, status_code=http.HTTPStatus.UNAUTHORIZED, msg='Invalid Credentials',
                             err_msg='Bearer Credentials')
    except PyJWTError as ex:
        raise_http_exception(request=request, status_code=http.HTTPStatus.UNAUTHORIZED, msg='Invalid Credentials',
                             err_msg=str(ex))


# schedule
scheduler = sched.scheduler(time.monotonic, time.sleep)


def run_scheduler_gateway(sch: sched.scheduler):
    print('Starting Run Scheduler Gateway')
    from gateway import set_env_details
    app = FastAPI()
    app.mongo_client = __get_mongo_client()
    request = Request(scope={'type': 'http', 'app': app})
    set_env_details(request=request, force_reset=True)
    app.mongo_client.close()
    scheduler.enter(14400, 1, run_scheduler_gateway, (sch,))


# 14400 = every 4 hours
def run_scheduler():
    print('Starting Scheduler!')
    scheduler.enter(14400, 1, run_scheduler_gateway, (scheduler,))
    scheduler.run()


def stop_scheduler():
    for event in scheduler.queue:
        scheduler.cancel(event)
    print('Stopped Scheduler!')


# other utility functions
def is_production():
    return APP_ENV == 'production'


def raise_http_exception(request: Request, status_code: http.HTTPStatus | int, msg: str, err_msg: str = ''):
    print('[ {} ] | RESPONSE::: Outgoing: [ {} ] | Status: [ {} ]'.format(get_trace_int(request), request.url,
                                                                          status_code))
    raise HTTPException(status_code=status_code, detail={'msg': msg, 'errMsg': err_msg})


def get_trace_int(request: Request):
    try:
        return request.state.trace_int
    except AttributeError:
        return ''
