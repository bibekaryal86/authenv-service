from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import users as users_api
import utils as utils


@asynccontextmanager
async def lifespan(application: FastAPI):
    utils.validate_input()
    utils.startup_db_client(application)
    yield
    utils.shutdown_db_client(application)


app = FastAPI(
    title='Authenticate Service',
    description='Generic Global Authentication and Gateway Service to Overcome CORS Errors in React SPAs',
    version='1.0.1',
    lifespan=lifespan,
    openapi_url=None if utils.is_production() else '/authenv-service/openapi.json',
    docs_url=None if utils.is_production() else '/authenv-service/docs',
    redoc_url=None if utils.is_production() else '/authenv-service/redoc'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(users_api.router)


@app.get('/authenv-service/tests/ping', tags=['Main'], summary='Ping Application')
async def tests_ping():
    return {'test': 'successful'}


if __name__ == '__main__':
    port = 8080
    uvicorn.run(app, port=port, host='0.0.0.0')
