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

import requests

from app.commons.logger_services.logger_factory_service import SrvLoggerFactory
from app.config import ConfigClass
from app.models.base import EAPIResponseCode
from app.resources.error_handler import APIException

logger = SrvLoggerFactory('api_copy_request').get_logger()


def trigger_copy_pipeline(
    request_id: str,
    project_geid: str,
    source_geid: str,
    destination_geid: str,
    entity_geids: list[str],
    username: str,
    session_id: str,
    auth: dict,
) -> dict:
    copy_data = {
        'payload': {
            'targets': [{'geid': i} for i in entity_geids],
            'destination': destination_geid,
            'source': source_geid,
            'request_id': request_id,
        },
        'operator': username,
        'operation': 'copy',
        'project_geid': project_geid,
        'session_id': session_id,
    }
    response = requests.post(ConfigClass.DATA_UTILITY_SERVICE + 'files/actions', json=copy_data, headers=auth)
    if response.status_code >= 300:
        error_msg = f'Failed to start copy pipeline: {response.content}'
        logger.error(error_msg)
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    return response.json()['result']
