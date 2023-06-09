import logging
import threading
from contextlib import asynccontextmanager

import auth_users as users_api
import env_props as env_props_api
import gateway as gateway_api
import utils as utils
import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import HTTPBasicCredentials
from utils import http_basic_security, validate_http_basic_credentials


@asynccontextmanager
async def lifespan(application: FastAPI):
    utils.validate_input()
    utils.startup_db_client(application)
    yield
    utils.shutdown_db_client(application)
    utils.stop_scheduler()


app = FastAPI(
    title='Authenticate Service',
    description='Generic Global Authentication and Gateway Service to Overcome CORS Errors in React SPAs',
    version='1.0.1',
    lifespan=lifespan,
    openapi_url=None if utils.is_production() else '/authenv-service/openapi.json',
    docs_url=None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(users_api.router)
app.include_router(env_props_api.router)
app.include_router(gateway_api.router)

scheduler_thread = threading.Thread(target=utils.run_scheduler)
scheduler_thread.start()


@app.get('/authenv-service/tests/ping', tags=['Main'], summary='Ping Application')
def tests_ping():
    return {'test': 'successful'}


@app.get('/authenv-service/tests/reset', tags=['Main'], summary='Reset Cache')
def tests_reset(request: Request):
    gateway_api.set_env_details(request=request, force_reset=True)
    return {'reset': 'successful'}


@app.get("/authenv-service/docs", include_in_schema=False)
async def custom_docs_url(request: Request,
                          http_basic_credentials: HTTPBasicCredentials = Depends(http_basic_security)):
    validate_http_basic_credentials(request, http_basic_credentials)
    root_path = request.scope.get("root_path", "").rstrip("/")
    openapi_url = root_path + app.openapi_url
    return get_swagger_ui_html(openapi_url=openapi_url, title=app.title)


if __name__ == '__main__':
    port = 8080
    host = '0.0.0.0'
    uvicorn.run(app, port=port, host='0.0.0.0', log_level=logging.WARNING)
