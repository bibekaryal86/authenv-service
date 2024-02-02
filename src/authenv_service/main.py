import logging
import os
import time
from contextlib import asynccontextmanager

import auth_users as users_api
import constants as constants
import env_props as env_props_api
import gateway as gateway_api
import utils as utils
import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import HTTPBasicCredentials
from logger import Logger

log = Logger(logging.getLogger(__name__))


@asynccontextmanager
async def lifespan(application: FastAPI):
    constants.validate_input()
    utils.startup_db_client(application)
    stop_event, schedule_thread = utils.start_scheduler()
    yield
    utils.shutdown_db_client(application)
    utils.stop_scheduler(stop_event, schedule_thread)


app = FastAPI(
    title="Authenticate Service",
    description="Generic Global Authentication and Gateway "
    "Service to Overcome CORS Errors in React SPAs",
    version="1.0.1",
    lifespan=lifespan,
    openapi_url=None if utils.is_production() else "/authenv-service/openapi.json",
    docs_url=None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(users_api.router)
app.include_router(env_props_api.router)
app.include_router(gateway_api.router)


@app.middleware("http")
async def log_request_response(request: Request, call_next):
    log.info(f"Receiving [ {request.method} ] URL [ {request.url} ]")
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["x-process-time"] = str(process_time)
    log.info(
        f"Returning [ {request.method} ] Status Code [ {response.status_code} ] "
        f"URL [ {request.url} ] AFTER [ {format(process_time, '.4f')}ms]"
    )
    return response


@app.get("/authenv-service/tests/ping", tags=["Main"], summary="Ping Application")
def ping():
    return {"test": "successful"}


@app.get("/authenv-service/tests/reset", tags=["Main"], summary="Reset Cache")
def reset(request: Request):
    gateway_api.set_env_details(request=request, force_reset=True)
    return {"reset": "successful"}


@app.get("/authenv-service/tests/log-level", tags=["Main"], summary="Set Log Level")
def log_level(level: utils.LogLevelOptions):
    log_level_to_set = logging.getLevelNamesMapping().get(level)
    log.set_level(log_level_to_set)
    utils.log.set_level(log_level_to_set)
    gateway_api.log.set_level(log_level_to_set)
    return {"set": "successful"}


@app.get("/authenv-service/docs", include_in_schema=False)
async def custom_docs_url(
    request: Request,
    http_basic_credentials: HTTPBasicCredentials = Depends(utils.http_basic_security),
):
    utils.validate_http_basic_credentials(request, http_basic_credentials)
    root_path = request.scope.get("root_path", "").rstrip("/")
    openapi_url = root_path + app.openapi_url
    return get_swagger_ui_html(openapi_url=openapi_url, title=app.title)


if __name__ == "__main__":
    port = os.getenv(constants.ENV_APP_PORT, "9999")
    uvicorn.run(app, port=int(port), host="0.0.0.0", log_level=logging.WARNING)
