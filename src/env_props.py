import http
import os
import secrets

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
from pydantic import parse_obj_as
from pydantic.class_validators import Optional
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from utils import BASIC_AUTH_USR, BASIC_AUTH_PWD

router = APIRouter(
    prefix="/authenv-service/env-props",
    tags=["Env Properties"]
)

security = HTTPBasic()


class EnvDetails(BaseModel):
    name: str
    string_value: Optional[str] = Field(alias='stringValue')
    list_value: Optional[list] = Field(alias='listValue')
    map_value: Optional[dict] = Field(alias='mapValue')


class EnvDetailsResponse(BaseModel):
    msg: Optional[str]


@router.get("/{appname}", response_model=list[EnvDetails], status_code=http.HTTPStatus.OK)
def find(request: Request, appname: str, http_basic_credentials: HTTPBasicCredentials = Depends(security)):
    __validate_request(http_basic_credentials)
    return __find_env_details(request, app_name=appname)


@router.post("/{appname}", response_model=EnvDetailsResponse, status_code=http.HTTPStatus.CREATED)
def save(request: Request, appname: str, env_detail: EnvDetails,
         http_basic_credentials: HTTPBasicCredentials = Depends(security)):
    __validate_request(http_basic_credentials)
    __save_env_details(request=request, app_name=appname, env_detail=env_detail)
    return EnvDetailsResponse(msg='Saved Successfully!')


@router.delete("/{appname}/{propname}", response_model=EnvDetailsResponse, status_code=http.HTTPStatus.ACCEPTED)
def remove(request: Request, appname: str, propname: str,
           http_basic_credentials: HTTPBasicCredentials = Depends(security)):
    __validate_request(http_basic_credentials)
    __remove_env_details(request=request, app_name=appname, prop_name=propname)
    return EnvDetailsResponse(msg='Removed Successfully')


def __validate_request(http_basic_credentials: HTTPBasicCredentials):
    valid_username = os.getenv(BASIC_AUTH_USR)
    valid_password = os.getenv(BASIC_AUTH_PWD)
    input_username = http_basic_credentials.username
    input_password = http_basic_credentials.password
    is_correct_username = secrets.compare_digest(valid_username.encode('utf-8'), input_username.encode('utf-8'))
    is_correct_password = secrets.compare_digest(valid_password.encode('utf-8'), input_password.encode('utf-8'))
    if not (is_correct_username and is_correct_password):
        raise HTTPException(status_code=http.HTTPStatus.UNAUTHORIZED, detail='Invalid Credentials!')


def __env_details_collection(request: Request, app_name: str):
    mongo_client = request.app.mongo_client
    mongo_database = mongo_client.env_details
    mongo_collection = mongo_database[app_name]
    return mongo_collection


def __find_env_details(request, app_name):
    mongo_collection: Collection = __env_details_collection(request=request, app_name=app_name)
    env_details_output: list[EnvDetails] = []
    try:
        env_details = mongo_collection.find()
        for env_detail in env_details:
            env_detail_output = parse_obj_as(EnvDetails, env_detail)
            env_details_output.append(env_detail_output)
        return env_details_output
    except PyMongoError as ex:
        raise HTTPException(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                            detail={'msg': f'Error retrieving env properties: {app_name}', 'errMsg': str(ex)})


def __save_env_details(request, app_name, env_detail):
    mongo_collection: Collection = __env_details_collection(request=request, app_name=app_name)
    try:
        mongo_collection.insert_one(jsonable_encoder(env_detail, exclude_none=True))
        return __find_env_details(request=request, app_name=app_name)
    except PyMongoError as ex:
        raise HTTPException(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                            detail={'msg': f'Error saving env properties: {app_name}', 'errMsg': str(ex)})


def __remove_env_details(request, app_name, prop_name):
    mongo_collection: Collection = __env_details_collection(request=request, app_name=app_name)
    try:
        delete_result = mongo_collection.delete_one({'name': prop_name})
        if delete_result.deleted_count == 0:
            raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                                detail={'msg': f'Prop Not Found: {app_name} -- {prop_name}'})
        return __find_env_details(request=request, app_name=app_name)
    except PyMongoError as ex:
        raise HTTPException(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                            detail={'msg': f'Error removing env properties: {app_name}', 'errMsg': str(ex)})
