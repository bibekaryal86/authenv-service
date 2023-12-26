import http
import json
import logging
import random
import re
import time
from typing import Callable, Optional

import requests
from constants import (
    APP_ENV,
    GATEWAY_AUTH_CONFIGS,
    GATEWAY_AUTH_EXCLUSIONS,
    GATEWAY_BASE_URLS,
    RESTRICTED_HEADERS,
)
from env_props import EnvDetails, find_internal
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.security import HTTPAuthorizationCredentials
from logger import Logger
from utils import get_trace_int, raise_http_exception, validate_http_auth_credentials

log = Logger(logging.getLogger(__name__), __name__)


class GatewayAPIRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def log_auth_filter_handler(request: Request) -> Response:
            start_time = time.time()
            request.state.trace_int = random.randint(1000, 9999)
            if request.method != http.HTTPMethod.OPTIONS:
                log.info(
                    "[ {} ] | REQUEST::: Incoming: [ {} ] | Method: [ {} ]".format(
                        request.state.trace_int, request.url, request.method
                    ),
                )
                validate_request_header_auth(request)
                # response is logged in __gateway method below
            response = await original_route_handler(request)
            end_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(end_time)
            return response

        return log_auth_filter_handler


router = APIRouter(
    prefix="/gateway",
    route_class=GatewayAPIRoute,
    include_in_schema=False,
    tags=["Gateway"],
)

env_details_cache: list[EnvDetails] = []
routes_map_cache: dict = {}
auth_exclusions_cache: list[str] = []
auth_configs_cache: dict = {}


def set_env_details(request: Request, force_reset: bool = False):
    if force_reset or len(env_details_cache) == 0:
        # reset
        auth_configs_cache.clear()
        auth_exclusions_cache.clear()
        routes_map_cache.clear()
        env_details_cache.clear()
        env_details = find_internal(request=request, appname="app_authgateway")
        # set
        env_details_cache.extend(env_detail for env_detail in env_details)
        __auth_configs(request)
        __auth_exclusions(request)
        __routes_map(request)
    return env_details_cache


def validate_request_header_auth(request: Request) -> str:
    auth_exclusions = __auth_exclusions(request)
    for auth_exclusion in auth_exclusions:
        if auth_exclusion in str(request.url):
            return "auth_exclusion"

    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        raise_http_exception(
            request=request,
            status_code=http.HTTPStatus.UNAUTHORIZED,
            error="Invalid Credentials / Missing Credentials",
        )
    access_token = auth_header.split()
    http_auth_credentials = HTTPAuthorizationCredentials(
        scheme=access_token[0], credentials=access_token[1]
    )
    return validate_http_auth_credentials(request, http_auth_credentials)


@router.options("/{appname}/{path:path}", status_code=http.HTTPStatus.OK)
def gateway_options(appname: str, path: str):
    log.debug(f"Options Request: {appname}/{path}")


@router.get("/{appname}/{path:path}", status_code=http.HTTPStatus.OK)
def gateway_get(request: Request, appname: str, path: str, body: Optional[dict] = None):
    return __gateway(request=request, appname=appname, path=path, body=body)


@router.post("/{appname}/{path:path}", status_code=http.HTTPStatus.OK)
def gateway_post(
    request: Request, appname: str, path: str, body: Optional[dict] = None
):
    return __gateway(request=request, appname=appname, path=path, body=body)


@router.put("/{appname}/{path:path}", status_code=http.HTTPStatus.OK)
def gateway_put(request: Request, appname: str, path: str, body: Optional[dict] = None):
    return __gateway(request=request, appname=appname, path=path, body=body)


@router.patch("/{appname}/{path:path}", status_code=http.HTTPStatus.OK)
def gateway_patch(
    request: Request, appname: str, path: str, body: Optional[dict] = None
):
    return __gateway(request=request, appname=appname, path=path, body=body)


@router.delete("/{appname}/{path:path}", status_code=http.HTTPStatus.OK)
def gateway_delete(
    request: Request, appname: str, path: str, body: Optional[dict] = None
):
    return __gateway(request=request, appname=appname, path=path, body=body)


def __gateway(request: Request, appname: str, path: str, body: dict):
    base_url = __base_url(request, appname)

    if base_url is None:
        raise_http_exception(
            request=request,
            status_code=http.HTTPStatus.SERVICE_UNAVAILABLE,
            error=f"Error! Route for {appname} Not Found!! Please Try Again!!!",
        )

    outgoing_url = base_url + "/" + appname + "/" + path
    http_method = request.method
    request_body = None if body is None else json.dumps(body)
    request_headers = dict()
    for k, v in request.headers.items():
        if k.lower() not in RESTRICTED_HEADERS:
            request_headers[k] = v

    try:
        response = requests.request(
            method=http_method,
            url=outgoing_url,
            params=request.query_params,
            headers=request_headers,
            auth=__auth_config(request),
            data=request_body,
        )
        log.info(
            "[ {} ] | RESPONSE::: Outgoing: [ {} ] | Status: [ {} ]".format(
                get_trace_int(request), outgoing_url, response.status_code
            ),
        )
        content = None if response.json() is None else response.json()
        response_headers = dict()
        for k, v in response.headers.items():
            # Custom headers typically have an "X-" prefix
            if "x-" in k.lower():
                response_headers[k] = v
        return JSONResponse(
            content=content, status_code=response.status_code, headers=response_headers
        )
    except Exception as ex:
        log.info(
            "[ {} ] | CONNECTION_ERROR::: Outgoing: [ {} ]---[{}]".format(
                get_trace_int(request), outgoing_url, str(ex)
            ),
        )
        raise HTTPException(
            status_code=http.HTTPStatus.BAD_GATEWAY, detail={"error": str(ex)}
        )


def __routes_map(request: Request):
    if len(routes_map_cache) == 0:
        env_details = set_env_details(request=request)
        env_detail_base_urls = list(
            filter(
                lambda env_detail: env_detail.name == GATEWAY_BASE_URLS.format(APP_ENV),
                env_details,
            )
        )
        base_urls = env_detail_base_urls[0].map_value
        for k, v in base_urls.items():
            appname = re.findall(pattern="/(.*?)/", string=k)[0]
            routes_map_cache.update({appname: v})
    return routes_map_cache


def __base_url(request: Request, appname: str):
    routes_map = __routes_map(request)
    return routes_map.get(appname)


def __auth_exclusions(request: Request):
    if len(auth_exclusions_cache) == 0:
        env_details = set_env_details(request=request)
        env_details_auth_exclusions = list(
            filter(
                lambda env_detail: env_detail.name == GATEWAY_AUTH_EXCLUSIONS,
                env_details,
            )
        )
        auth_exclusions = env_details_auth_exclusions[0].list_value
        auth_exclusions_cache.extend(
            auth_exclusion for auth_exclusion in auth_exclusions
        )
    return auth_exclusions_cache


def __auth_configs(request: Request):
    if len(auth_configs_cache) == 0:
        env_details = set_env_details(request=request)
        env_details_auth_configs = list(
            filter(
                lambda env_detail: env_detail.name == GATEWAY_AUTH_CONFIGS, env_details
            )
        )
        auth_configs = env_details_auth_configs[0].map_value
        auth_configs_cache.update(auth_configs)
    return auth_configs_cache


def __auth_config(request: Request):
    auth_configs = __auth_configs(request)
    appname = request.path_params.get("appname")

    if appname:
        appname_user_prop_name = appname + "-usr"
        appname_pwd_prop_name = appname + "-pwd"
        username = auth_configs.get(appname_user_prop_name)
        password = auth_configs.get(appname_pwd_prop_name)

        if username and password:
            return username, password
