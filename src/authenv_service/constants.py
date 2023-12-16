import datetime
import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Constants
ENV_APP_PORT = "APP_PORT"
SERVICE_AUTH_USR = "-usr"
SERVICE_AUTH_PWD = "-pwd"
GATEWAY_AUTH_EXCLUSIONS = "authExclusions"
GATEWAY_AUTH_CONFIGS = "authConfigs"
GATEWAY_ROUTE_PATHS = "routePaths"
GATEWAY_BASE_URLS = "baseUrls_{}"
SCHEDULER_ENV_DETAILS_EXECUTE_TIME = [

    datetime.time(0, 0, 1).strftime("%H:%M:%S"),
    datetime.time(6, 0, 1).strftime("%H:%M:%S"),
    datetime.time(12, 0, 1).strftime("%H:%M:%S"),
    datetime.time(6, 0, 1).strftime("%H:%M:%S"),
]
# https://github.com/bibekaryal86/pets-gateway-simple/blob/main/app/src/main/java/pets/gateway/app/util/Util.java#L42
RESTRICTED_HEADERS = [
    "accept-charset",
    "accept-encoding",
    "access-control-request-headers",
    "access-control-request-method",
    "connection",
    "content-length",
    "cookie",
    "cookie2",
    "content-transfer-encoding",
    "date",
    "expect",
    "host",
    "keep-alive",
    "origin",
    "referer",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "user-agent",
    "via",
    "authorization",  # auth is set separately using auth parameter
]


# ENVIRONMENT VARIABLES
class Settings(BaseSettings):
    if os.getenv("IS_PYTEST"):
        model_config = SettingsConfigDict(env_file=".env.example", extra="allow")
    else:
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
REPO_HOME = get_settings().repo_home


# startup
def validate_input():
    missing_variables = []

    if APP_ENV is None:
        missing_variables.append("APP_ENV")

    if SECRET_KEY is None:
        missing_variables.append("SECRET_KEY")

    if MONGODB_USR_NAME is None:
        missing_variables.append("MONGODB_USR_NAME")

    if MONGODB_USR_PWD is None:
        missing_variables.append("MONGODB_USR_PWD")

    if BASIC_AUTH_USR is None:
        missing_variables.append("BASIC_AUTH_USR")

    if BASIC_AUTH_PWD is None:
        missing_variables.append("BASIC_AUTH_PWD")

    if REPO_HOME is None:
        missing_variables.append("REPO_HOME")

    if len(missing_variables) != 0:
        raise ValueError(
            "The following env variables are missing: {}".format(missing_variables)
        )
