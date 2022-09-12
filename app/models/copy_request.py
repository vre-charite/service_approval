# Copyright 2022 Indoc Research
# 
# Licensed under the EUPL, Version 1.2 or – as soon they
# will be approved by the European Commission - subsequent
# versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the
# Licence.
# You may obtain a copy of the Licence at:
# 
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12
# 
# Unless required by applicable law or agreed to in
# writing, software distributed under the Licence is
# distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.
# See the Licence for the specific language governing
# permissions and limitations under the Licence.
# 

import json
import uuid

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator

from app.resources.error_handler import APIException
from .base import APIResponse
from .base import EAPIResponseCode
from .base import PaginationRequest


class POSTRequest(BaseModel):
    entity_geids: list[str]
    destination_geid: str
    source_geid: str
    note: str
    submitted_by: str

    @validator('note')
    def valid_note(cls, value):
        if value == "":
            raise APIException(EAPIResponseCode.bad_request.value, "Note is required")
        return value


class POSTRequestResponse(APIResponse):
    result: dict = Field({}, example={
        'code': 200,
        'error_msg': '',
        'num_of_pages': 1,
        'page': 0,
        'result': "success",
        'total': 1
    })


class GETRequest(PaginationRequest):
    status: str
    submitted_by: str = None


class GETRequestResponse(APIResponse):
    result: dict = Field({}, example={
        'code': 200,
        'error_msg': '',
        'num_of_pages': 1,
        'page': 0,
        'result': [],
        'total': 1
    })


class GETRequestFiles(PaginationRequest):
    request_id: uuid.UUID
    parent_geid: str = ""
    query: str = "{}"
    partial: str = "[]"
    order_by: str = "uploaded_at"

    @validator('query', 'partial')
    def valid_json(cls, value):
        try:
            value = json.loads(value)
        except Exception as e:
            error_msg = f"query or partial json is not valid"
            raise APIException(EAPIResponseCode.bad_request.value, f"Invalid json: {value}")
        return value


class GETRequestFilesResponse(APIResponse):
    result: dict = Field({}, example={
        'code': 200,
        'error_msg': '',
        'num_of_pages': 1,
        'page': 0,
        'result': [],
        'total': 1
    })


class PUTRequest(BaseModel):
    request_id: uuid.UUID
    status: str
    review_notes: str = ""
    username: str

    @validator('status')
    def valid_status(cls, value):
        if value != "complete":
            raise APIException(EAPIResponseCode.bad_request.value, "invalid review status")
        return value


class PUTRequestFiles(BaseModel):
    request_id: uuid.UUID
    review_status: str
    session_id: str
    username: str

    @validator('review_status')
    def valid_review_status(cls, value):
        if value not in ["approved", "denied"]:
            raise APIException(EAPIResponseCode.bad_request.value, "invalid review status")
        return value


class PATCHRequestFiles(BaseModel):
    entity_geids: list[str]
    request_id: uuid.UUID
    review_status: str
    username: str
    session_id: str

    @validator('review_status')
    def valid_review_status(cls, value):
        if value not in ["approved", "denied"]:
            raise APIException(EAPIResponseCode.bad_request.value, "invalid review status")
        return value


class PUTRequestFilesResponse(APIResponse):
    result: dict = Field({}, example={
        'code': 200,
        'error_msg': '',
        'num_of_pages': 1,
        'page': 0,
        'result': [],
        'total': 1
    })


class GETRequestPending(BaseModel):
    request_id: uuid.UUID


class GETPendingResponse(APIResponse):
    result: dict = Field({}, example={
        'code': 200,
        'error_msg': '',
        'num_of_pages': 1,
        'page': 0,
        'result': {
            "pending_count": 1,
            "pending_entities": ["geid"],
        },
        'total': 1
    })
