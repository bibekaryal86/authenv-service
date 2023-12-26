import http
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPBasicCredentials
from pydantic import BaseModel, Field, TypeAdapter
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from utils import (
    get_err_msg,
    http_basic_security,
    raise_http_exception,
    validate_http_basic_credentials,
)

router = APIRouter(prefix="/authenv-service/env-props", tags=["Env Properties"])


class EnvDetails(BaseModel):
    name: str
    string_value: Optional[str] = Field(alias="stringValue", default="")
    list_value: Optional[list] = Field(alias="listValue", default=[])
    map_value: Optional[dict] = Field(alias="mapValue", default={})


class EnvDetailsResponse(BaseModel):
    msg: Optional[str] = None


@router.get(
    "/{appname}", response_model=list[EnvDetails], status_code=http.HTTPStatus.OK
)
def find(
    request: Request,
    appname: str,
    http_basic_credentials: HTTPBasicCredentials = Depends(http_basic_security),
):
    validate_http_basic_credentials(request, http_basic_credentials)
    return __find_env_details(request, app_name=appname)


def find_internal(
    request: Request,
    appname: str,
):
    return __find_env_details(request, app_name=appname)


@router.post(
    "/{appname}", response_model=EnvDetailsResponse, status_code=http.HTTPStatus.CREATED
)
def save(
    request: Request,
    appname: str,
    env_detail: EnvDetails,
    http_basic_credentials: HTTPBasicCredentials = Depends(http_basic_security),
):
    validate_http_basic_credentials(request, http_basic_credentials)
    __save_env_details(request=request, app_name=appname, env_detail=env_detail)
    return EnvDetailsResponse(msg="Saved Successfully!")


@router.delete(
    "/{appname}/{propname}",
    response_model=EnvDetailsResponse,
    status_code=http.HTTPStatus.ACCEPTED,
)
def remove(
    request: Request,
    appname: str,
    propname: str,
    http_basic_credentials: HTTPBasicCredentials = Depends(http_basic_security),
):
    validate_http_basic_credentials(request, http_basic_credentials)
    __remove_env_details(request=request, app_name=appname, prop_name=propname)
    return EnvDetailsResponse(msg="Removed Successfully")


def __env_details_collection(request: Request, app_name: str):
    mongo_client = request.app.mongo_client
    mongo_database = mongo_client.env_details
    mongo_collection = mongo_database[app_name]
    return mongo_collection


def __find_env_details(request, app_name):
    mongo_collection: Collection = __env_details_collection(
        request=request, app_name=app_name
    )
    env_details_output: list[EnvDetails] = []
    try:
        env_details = mongo_collection.find()
        env_details_type_adapter = TypeAdapter(EnvDetails)
        for env_detail in env_details:
            env_detail_output = env_details_type_adapter.validate_python(env_detail)
            env_details_output.append(env_detail_output)
        return env_details_output
    except PyMongoError as ex:
        raise_http_exception(
            request=request,
            status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
            error=get_err_msg(f"Error retrieving env properties: {app_name}", str(ex)),
        )


def __save_env_details(request, app_name, env_detail):
    mongo_collection: Collection = __env_details_collection(
        request=request, app_name=app_name
    )
    try:
        document_filter = {"name": env_detail.name}
        document_value = __get_document_value_for_upsert(env_detail)
        mongo_collection.update_one(
            filter=document_filter, update=document_value, upsert=True
        )
        return __find_env_details(request=request, app_name=app_name)
    except PyMongoError as ex:
        raise_http_exception(
            request=request,
            status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
            error=get_err_msg(f"Error saving env properties: {app_name}", str(ex)),
        )


def __remove_env_details(request, app_name, prop_name):
    mongo_collection: Collection = __env_details_collection(
        request=request, app_name=app_name
    )
    try:
        delete_result = mongo_collection.delete_one({"name": prop_name})
        if delete_result.deleted_count == 0:
            raise_http_exception(
                request=request,
                status_code=http.HTTPStatus.NOT_FOUND,
                error=f"Prop Not Found: {app_name} -- {prop_name}",
            )
        return __find_env_details(request=request, app_name=app_name)
    except PyMongoError as ex:
        raise_http_exception(
            request=request,
            status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
            error=get_err_msg(f"Error removing env properties: {app_name}", str(ex)),
        )


def __get_document_value_for_upsert(env_detail: EnvDetails):
    document_value = {}
    document_value_set = {"name": env_detail.name}
    if env_detail.string_value:
        document_value_set["stringValue"] = env_detail.string_value
    if env_detail.list_value:
        document_value_set["listValue"] = env_detail.list_value
    if env_detail.map_value:
        document_value_set["mapValue"] = env_detail.map_value
    document_value["$set"] = document_value_set
    return document_value
