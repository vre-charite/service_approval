import requests

from app.commons.logger_services.logger_factory_service import SrvLoggerFactory
from app.config import ConfigClass
from app.models.copy_request_sql import RequestModel
from app.resources.error_handler import APIException


logger = SrvLoggerFactory("api_copy_request").get_logger()


def trigger_copy_pipeline(request_obj: RequestModel, entity_geids: list[str], username: str, session_id: str,
        auth: dict) -> dict:
    copy_data = {
        "payload": {
            "targets": [{"geid": i} for i in entity_geids],
            "destination": request_obj.destination_geid,
            "request_id": str(request_obj.id),
        },
        "operator": username,
        "operation": "copy",
        "project_geid": request_obj.project_geid,
        "session_id": session_id
    }
    response = requests.post(
        ConfigClass.DATA_UTILITY_SERVICE + "files/actions",
        json=copy_data,
        headers=auth
    )
    if response.status_code >= 300:
        error_msg = f"Failed to start copy pipeline: {response.content}"
        logger.error(error_msg)
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    return response.json()["result"]

