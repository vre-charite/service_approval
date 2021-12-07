from pydantic import BaseModel, Field, validator
from .base import APIResponse, PaginationRequest, EAPIResponseCode
from app.resources.error_handler import APIException
import json


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
    request_id: str
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
    request_id: str
    status: str
    review_notes: str = ""
    username: str

    @validator('status')
    def valid_status(cls, value):
        if value != "complete":
            raise APIException(EAPIResponseCode.bad_request.value, "invalid review status")
        return value

class PUTRequestFiles(BaseModel):
    request_id: str
    review_status: str
    session_id: str
    username: str

    @validator('review_status')
    def valid_review_status(cls, value):
        if not value in ["approved", "denied"]:
            raise APIException(EAPIResponseCode.bad_request.value, "invalid review status")
        return value

class PATCHRequestFiles(BaseModel):
    entity_geids: list[str]
    request_id: str
    review_status: str
    username: str
    session_id: str

    @validator('review_status')
    def valid_review_status(cls, value):
        if not value in ["approved", "denied"]:
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
    request_id: str

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
