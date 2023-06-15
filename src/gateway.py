import http
import os
import random
from typing import Callable

from fastapi import APIRouter, Request, Response
from fastapi.routing import APIRoute

from env_props import EnvDetails, find
from utils import validate_request_header_auth, APP_ENV, GATEWAY_BASE_URLS, raise_http_exception, get_trace_int


class GatewayAPIRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def log_auth_filter_handler(request: Request) -> Response:
            request.state.trace_int = random.randint(1000, 9999)
            if request.method != http.HTTPMethod.OPTIONS:
                print(
                    '[ {} ] | REQUEST::: Incoming: [ {} ] | Method: [ {} ]'.format(request.state.trace_int, request.url,
                                                                                   request.method))
                validate_request_header_auth(request)
                # response is logged in __gateway method below
            return await original_route_handler(request)

        return log_auth_filter_handler


router = APIRouter(
    prefix='/gateway',
    route_class=GatewayAPIRoute,
    include_in_schema=False,
    tags=["Gateway"]
)

env_details_cache: list[EnvDetails] = []
routes_map_cache: dict = {}


def set_env_details(request: Request, force_reset: bool = False):
    if force_reset or len(env_details_cache) == 0:
        env_details_cache.clear()
        env_details = find(request=request, appname='app_authgateway', is_validate_credentials=False)
        env_details_cache.extend(env_detail for env_detail in env_details)
    return env_details_cache


@router.options('/{appname}/{path:path}', status_code=http.HTTPStatus.OK)
def gateway_options(appname: str, path: str):
    print(f'Options Request: {appname}/{path}')


@router.get('/{appname}/{path:path}', status_code=http.HTTPStatus.OK)
def gateway_get(request: Request, appname: str, path: str):
    return __gateway(request=request, appname=appname, path=path)


@router.post('/{appname}/{path:path}', status_code=http.HTTPStatus.OK)
def gateway_post(request: Request, appname: str, path: str):
    return __gateway(request=request, appname=appname, path=path)


@router.put('/{appname}/{path:path}', status_code=http.HTTPStatus.OK)
def gateway_put(request: Request, appname: str, path: str):
    return __gateway(request=request, appname=appname, path=path)


@router.patch('/{appname}/{path:path}', status_code=http.HTTPStatus.OK)
def gateway_patch(request: Request, appname: str, path: str):
    return __gateway(request=request, appname=appname, path=path)


@router.delete('/{appname}/{path:path}', status_code=http.HTTPStatus.OK)
def gateway_delete(request: Request, appname: str, path: str):
    return __gateway(request=request, appname=appname, path=path)


def __gateway(request: Request, appname: str, path: str):
    base_url = __base_url(request, appname)

    if base_url is None:
        raise_http_exception(request=request, status_code=http.HTTPStatus.SERVICE_UNAVAILABLE,
                             msg=f'Error! Route for {appname} Not Found!! Please Try Again!!!')

    query_params = str(request.query_params)
    outgoing_url = base_url + '/' + appname + '/' + path if len(query_params) == 0 \
        else base_url + '/' + appname + '/' + path + '?' + query_params

    print('[ {} ] | RESPONSE::: Outgoing: [ {} ] | Status: [ {} ]'.format(get_trace_int(request), outgoing_url,
                                                                          200))
    return {'gateway': 'successful'}


def __routes_map(request: Request):
    if len(routes_map_cache) == 0:
        app_env = os.getenv(APP_ENV)
        env_details = set_env_details(request=request)
        env_detail_base_urls = list(filter(lambda env_detail: env_detail.name == GATEWAY_BASE_URLS.format(app_env),
                                           env_details))
        base_urls = env_detail_base_urls[0].map_value
        routes_map_cache.update(base_urls)
    return routes_map_cache


def __base_url(request: Request, appname: str):
    routes_map = __routes_map(request)
    for k, v in routes_map.items():
        if appname in k:
            return v
    return None
