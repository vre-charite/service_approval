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
from app.config import ConfigClass
from app.models.base import EAPIResponseCode
from app.resources.error_handler import APIException
from typing import List


def query_node(label: str, query_data: dict) -> dict:
    response = requests.post(ConfigClass.NEO4J_SERVICE + f"nodes/{label}/query", json=query_data)
    if response.status_code != 200:
        error_msg = f"Error calling Neo4j service: {response.json()}"
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    if not response.json():
        error_msg = f"{label} not found: {query_data}"
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.not_found.value)
    return response.json()[0]

def get_node_by_geid(geid: str) -> dict:
    response = requests.get(ConfigClass.NEO4J_SERVICE + f"nodes/geid/{geid}")
    if response.status_code != 200:
        error_msg = f"Error calling Neo4j service: {response.json()}"
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    if not response.json():
        error_msg = f"Folder not found"
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.not_found.value)
    return response.json()[0]

def bulk_get_by_geids(geids: List[str]) -> List[dict]:
    query_data = {"geids": geids}
    response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/query/geids", json=query_data)
    if response.status_code != 200:
        error_msg = f"Error calling Neo4j service: {response.json()}"
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    return response.json()["result"]


def get_parent(node: dict) -> dict:
    display_path = "/".join(node["display_path"].split("/")[:-1])
    query_data = {
        "query": {
            "labels": ["Folder", "Greenroom"],
            "display_path": display_path,
            "project_code": node["project_code"]
        }
    }
    response = requests.post(ConfigClass.NEO4J_SERVICE_V2 + "nodes/query", json=query_data)
    if response.status_code != 200:
        error_msg = f"Error calling Neo4j service: {response.json()}"
        logger.error(error_msg)
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    return response.json()["result"][0]


def get_files_recursive(folder_geid: str, all_files: list = None) -> list:
    if all_files is None:
        all_files = []
    query = {
        "start_label": "Folder",
        "end_labels": ["File", "Folder"],
        "query": {
            "start_params": {
                "global_entity_id": folder_geid,
            },
            "end_params": {
                "File": {
                    "archived": False,
                },
                "Folder": {
                    "archived": False,
                },
            },
        },
    }
    resp = requests.post(ConfigClass.NEO4J_SERVICE_V2 + "relations/query", json=query)
    for node in resp.json()["results"]:
        if "File" in node["labels"]:
            all_files.append(node)
        else:
            node["parent_folder_geid"] = folder_geid
            all_files.append(node)
            get_files_recursive(node["global_entity_id"], all_files=all_files)
    return all_files



