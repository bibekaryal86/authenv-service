import datetime
import http
import logging
import secrets
import threading
import time
from enum import Enum

import constants
import jwt
from fastapi import FastAPI, HTTPException, Request
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
)
from jwt import PyJWTError
from logger import Logger
from pymongo import MongoClient

log = Logger(logging.getLogger(__name__), __name__)


def startup_db_client(app: FastAPI):
    app.mongo_client = __get_mongo_client()
    log.info("Connected to MongoDb Client...")


def shutdown_db_client(app: FastAPI):
    app.mongo_client.close()
    log.info("Disconnected from MongoDb Client...")


def __get_mongo_client():
    connection_string = (
        "mongodb+srv://{}:{}@appdetails.bulegrc.mongodb.net/"
        "?retryWrites=true&w=majority".format(
            constants.MONGODB_USR_NAME, constants.MONGODB_USR_PWD
        )
    )
    return MongoClient(connection_string)


# security
http_basic_security = HTTPBasic()  # for main, env_props module
http_bearer_security = HTTPBearer()  # for users module


def validate_http_basic_credentials(
    request: Request, http_basic_credentials: HTTPBasicCredentials
):
    valid_username = constants.BASIC_AUTH_USR
    valid_password = constants.BASIC_AUTH_PWD
    input_username = http_basic_credentials.username
    input_password = http_basic_credentials.password
    is_correct_username = secrets.compare_digest(
        valid_username.encode("utf-8"), input_username.encode("utf-8")
    )
    is_correct_password = secrets.compare_digest(
        valid_password.encode("utf-8"), input_password.encode("utf-8")
    )
    if not (is_correct_username and is_correct_password):
        raise_http_exception(
            request=request,
            status_code=http.HTTPStatus.UNAUTHORIZED,
            error="Invalid Credentials / Basic Credentials",
        )


def encode_http_auth_credentials(username, source_ip):
    token_claim = {
        "username": username,
        "source_ip": source_ip,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    }
    return jwt.encode(payload=token_claim, key=constants.SECRET_KEY, algorithm="HS256")


def get_err_msg(msg: str, err_msg: str = ""):
    return msg + "\n" + err_msg


def validate_http_auth_credentials(
    request: Request,
    http_auth_credentials: HTTPAuthorizationCredentials,
    username: str = None,
) -> str:
    try:
        token_claims = jwt.decode(
            jwt=http_auth_credentials.credentials,
            key=constants.SECRET_KEY,
            algorithms=["HS256"],
        )
        token_username = token_claims.get("username")

        if username is None:
            return token_username
        elif username == token_username:
            return token_username

        raise_http_exception(
            request=request,
            status_code=http.HTTPStatus.UNAUTHORIZED,
            error="Invalid Credentials / Bearer Credentials",
        )
    except PyJWTError as ex:
        raise_http_exception(
            request=request,
            status_code=http.HTTPStatus.UNAUTHORIZED,
            error=get_err_msg("Invalid Credentials", str(ex)),
        )


# scheduler
def run_scheduler_gateway():
    log.info("Starting Run Scheduler Gateway...")
    from gateway import set_env_details

    app = FastAPI()
    app.mongo_client = __get_mongo_client()
    request = Request(scope={"type": "http", "app": app})
    set_env_details(request=request, force_reset=True)
    app.mongo_client.close()


def start_scheduler():
    log.info("Starting Scheduler Thread...")
    # run scheduler gateway to set cache for the first time
    run_scheduler_gateway()
    stop_event = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not stop_event.is_set():
                current_time = datetime.datetime.now().time().strftime("%H:%M:%S")
                if current_time in constants.SCHEDULER_ENV_DETAILS_EXECUTE_TIME:
                    run_scheduler_gateway()
                time.sleep(1)

    schedule_thread = ScheduleThread()
    schedule_thread.start()
    return stop_event, schedule_thread


def stop_scheduler(stop_event: threading.Event, schedule_thread: threading.Thread):
    stop_event.set()
    schedule_thread.join()
    log.info("Stopped Scheduler Thread...")


# other utility functions
def is_production():
    return constants.APP_ENV == "production"


def raise_http_exception(
    request: Request, status_code: http.HTTPStatus | int, error: str = ""
):
    log.info(
        "[ {} ] | RESPONSE::: Outgoing: [ {} ] | Status: [ {} ]".format(
            get_trace_int(request), request.url, status_code
        ),
    )
    raise HTTPException(status_code=status_code, detail={"error": error})


def get_trace_int(request: Request):
    try:
        return request.state.trace_int
    except AttributeError:
        return ""


class LogLevelOptions(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    ERROR = "ERROR"
