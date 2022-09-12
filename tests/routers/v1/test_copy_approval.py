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

import pytest

from app.config import ConfigClass
from tests.conftest import FILE_DATA, FOLDER_DATA, USER_DATA


@pytest.mark.dependency()
def test_create_request_200(test_client, requests_mocker, mock_project, mock_src_dest_folder, mock_user):
    # entity_geids file
    mock_data = {"result": [FILE_DATA, FOLDER_DATA]}
    requests_mocker.post(ConfigClass.NEO4J_SERVICE + "nodes/query/geids", json=mock_data)

    # mock notification
    requests_mocker.post(ConfigClass.EMAIL_SERVICE, json={})

    # mock get file list
    mock_data = {
        "results": [FILE_DATA]
    }
    requests_mocker.post(ConfigClass.NEO4J_SERVICE_V2 + "relations/query", json=mock_data)

    # mock get project admins
    mock_data = [{
        "start_node": USER_DATA,
        "end_node": {},
    }]
    requests_mocker.post(ConfigClass.NEO4J_SERVICE + "relations/query", json=mock_data)

    payload = {
        "entity_geids": ["approval_test_geid1", "approval_test_geid2"],
        "destination_geid": "dest_folder_geid",
        "source_geid": "src_folder_geid",
        "note": "testing",
        "submitted_by": "admin",
    }
    response = test_client.post("/v1/request/copy/approval_fake_project", json=payload)
    assert response.status_code == 200
    assert response.json()["result"]["destination_geid"] == "dest_folder_geid"
    assert response.json()["result"]["note"] == "testing"


@pytest.mark.dependency(depends=["test_create_request_200"])
def test_list_requests_200(test_client, requests_mocker):
    payload = {
        "status": "pending"
    }
    response = test_client.get("/v1/request/copy/approval_fake_project", params=payload)
    assert response.status_code == 200
    assert response.json()["result"][0]["destination_geid"] == "dest_folder_geid"
    assert response.json()["result"][0]["note"] == "testing"


@pytest.mark.dependency(depends=["test_create_request_200"])
def test_list_request_files_200(test_client, requests_mocker):
    payload = {
        "status": "pending"
    }
    response = test_client.get("/v1/request/copy/approval_fake_project", params=payload)
    request_obj = response.json()["result"][0]

    payload = {
        "request_id": request_obj["id"],
        "order_by": "name",
        "order_type": "desc",
    }
    response = test_client.get("/v1/request/copy/approval_fake_project/files", params=payload)
    assert response.status_code == 200
    assert len(response.json()["result"]["data"]) == 2
    assert len(response.json()["result"]["routing"]) == 0
    assert response.json()["result"]["data"][0]["name"] == "test_folder"
    assert response.json()["result"]["data"][1]["name"] == "test_file"


@pytest.mark.dependency(depends=["test_create_request_200"])
def test_list_request_files_query_200(test_client, requests_mocker):
    payload = {
        "status": "pending",
    }
    response = test_client.get("/v1/request/copy/approval_fake_project", params=payload)
    request_obj = response.json()["result"][0]

    payload = {
        "request_id": request_obj["id"],
        "order_by": "name",
        "order_type": "desc",
        "query": '{"name": "test_file"}',
        "parent_geid": "approval_test_geid2",
    }
    response = test_client.get("/v1/request/copy/approval_fake_project/files", params=payload)
    assert response.status_code == 200
    assert len(response.json()["result"]["data"]) == 1
    assert len(response.json()["result"]["routing"]) == 1
    assert response.json()["result"]["data"][0]["name"] == "test_file"


@pytest.mark.dependency(depends=["test_create_request_200"])
def test_approve_partial_files_200(test_client, requests_mocker):
    payload = {
        "status": "pending"
    }
    response = test_client.get("/v1/request/copy/approval_fake_project", params=payload)
    request_obj = response.json()["result"][0]

    # mock trigger pipeline
    requests_mocker.post(ConfigClass.DATA_UTILITY_SERVICE + "files/actions", json={"result": ""})

    payload = {
        "entity_geids": [
            "approval_test_geid1"
        ],
        "request_id": request_obj["id"],
        "review_status": "approved",
        "username": "admin",
        "session_id": "admin-123"
    }
    headers = {
        "Authorization": "fake",
        "Refresh-Token": "fake",
    }
    response = test_client.patch("/v1/request/copy/approval_fake_project/files", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["result"]["updated"] == 2
    assert response.json()["result"]["approved"] == 0
    assert response.json()["result"]["denied"] == 0


@pytest.mark.dependency(depends=["test_create_request_200"])
def test_approve_all_files_200(test_client, requests_mocker):
    payload = {
        "status": "pending"
    }
    response = test_client.get("/v1/request/copy/approval_fake_project", params=payload)
    request_obj = response.json()["result"][0]

    # mock trigger pipeline
    requests_mocker.post(ConfigClass.DATA_UTILITY_SERVICE + "files/actions", json={"result": ""})

    payload = {
        "request_id": request_obj["id"],
        "review_status": "approved",
        "username": "admin",
        "session_id": "admin-123"
    }
    headers = {
        "Authorization": "fake",
        "Refresh-Token": "fake",
    }
    response = test_client.put("/v1/request/copy/approval_fake_project/files", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["result"]["updated"] == 0
    assert response.json()["result"]["approved"] == 2
    assert response.json()["result"]["denied"] == 0


@pytest.mark.dependency(depends=["test_create_request_200"])
def test_complete_request_200(test_client, requests_mocker, mock_user, mock_project):
    payload = {
        "status": "pending"
    }
    response = test_client.get("/v1/request/copy/approval_fake_project", params=payload)
    request_obj = response.json()["result"][0]

    # mock notification
    requests_mocker.post(ConfigClass.EMAIL_SERVICE, json={})

    payload = {
        "request_id": request_obj["id"],
        "session_id": "admin-123",
        "status": "complete",
        "review_notes": "done",
        "username": "admin",
    }
    response = test_client.put("/v1/request/copy/approval_fake_project", json=payload)
    assert response.status_code == 200
    assert response.json()["result"]["status"] == "complete"
    assert response.json()["result"]["pending_count"] == 0


def test_create_request_sub_file_200(test_client, requests_mocker, mock_project, mock_src_dest_folder, mock_user):
    file_data = FILE_DATA.copy()
    file_data["global_entity_id"] = "approval_test_geid4"
    file_data["parent_folder_geid"] = ""

    # mock notification
    requests_mocker.post(ConfigClass.EMAIL_SERVICE, json={})

    mock_data = { "result": [file_data]}
    requests_mocker.post(ConfigClass.NEO4J_SERVICE + "nodes/query/geids", json=mock_data)

    mock_data = {
        "results": [file_data]
    }
    requests_mocker.post(ConfigClass.NEO4J_SERVICE_V2 + "relations/query", json=mock_data)

    # mock get project admins
    mock_data = [{
        "start_node": USER_DATA,
        "end_node": {},
    }]
    requests_mocker.post(ConfigClass.NEO4J_SERVICE + "relations/query", json=mock_data)

    payload = {
        "entity_geids": [file_data["global_entity_id"]],
        "destination_geid": "dest_folder_geid",
        "source_geid": "src_folder_geid",
        "note": "testing",
        "submitted_by": "admin",
    }
    response = test_client.post("/v1/request/copy/approval_fake_project", json=payload)
    assert response.status_code == 200
    assert response.json()["result"]["destination_geid"] == "dest_folder_geid"
    assert response.json()["result"]["note"] == "testing"


def test_deny_partial_files_200(test_client, requests_mocker):
    payload = {
        "status": "pending"
    }
    response = test_client.get("/v1/request/copy/approval_fake_project", params=payload)
    request_obj = response.json()["result"][0]

    payload = {
        "entity_geids": [
            FILE_DATA["global_entity_id"],
        ],
        "request_id": request_obj["id"],
        "review_status": "denied",
        "username": "admin",
        "session_id": "admin-123"
    }
    headers = {
        "Authorization": "fake",
        "Refresh-Token": "fake",
    }
    response = test_client.patch("/v1/request/copy/approval_fake_project/files", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["result"]["updated"] == 0
    assert response.json()["result"]["approved"] == 0
    assert response.json()["result"]["denied"] == 0


def test_partial_approved_200(test_client, requests_mocker, mock_src_dest_folder, mock_user, mock_project):
    FILE_DATA_2 = FILE_DATA.copy()
    FILE_DATA_2["global_entity_id"] = "approval_test_geid3"

    mock_data = {
        "results": [FILE_DATA_2]
    }
    requests_mocker.post(ConfigClass.NEO4J_SERVICE_V2 + "relations/query", json=mock_data)

    # mock trigger pipeline
    requests_mocker.post(ConfigClass.DATA_UTILITY_SERVICE + "files/actions", json={"result": ""})

    # mock get project admins
    mock_data = [{
        "start_node": USER_DATA,
        "end_node": {},
    }]
    requests_mocker.post(ConfigClass.NEO4J_SERVICE + "relations/query", json=mock_data)

    # entity_geids file
    mock_data = { "result": [FILE_DATA_2]}
    requests_mocker.post(ConfigClass.NEO4J_SERVICE + "nodes/query/geids", json=mock_data)

    # mock notification
    requests_mocker.post(ConfigClass.EMAIL_SERVICE, json={})

    payload = {
        "entity_geids": [FILE_DATA["global_entity_id"], FILE_DATA_2["global_entity_id"]],
        "destination_geid": "dest_folder_geid",
        "source_geid": "src_folder_geid",
        "note": "testing",
        "submitted_by": "admin",
    }
    response = test_client.post("/v1/request/copy/approval_fake_project", json=payload)
    assert response.status_code == 200
    assert response.json()["result"]["destination_geid"] == "dest_folder_geid"
    assert response.json()["result"]["note"] == "testing"

    request_obj = response.json()["result"]

    payload = {
        "entity_geids": [
            FILE_DATA["global_entity_id"]
        ],
        "request_id": request_obj["id"],
        "review_status": "denied",
        "username": "admin",
        "session_id": "admin-123"
    }
    headers = {
        "Authorization": "fake",
        "Refresh-Token": "fake",
    }
    response = test_client.patch("/v1/request/copy/approval_fake_project/files", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["result"]["updated"] == 0
    assert response.json()["result"]["approved"] == 0
    assert response.json()["result"]["denied"] == 0

    payload = {
        "entity_geids": [
            FILE_DATA_2["global_entity_id"]
        ],
        "request_id": request_obj["id"],
        "review_status": "approved",
        "username": "admin",
        "session_id": "admin-123"
    }
    headers = {
        "Authorization": "fake",
        "Refresh-Token": "fake",
    }
    response = test_client.patch("/v1/request/copy/approval_fake_project/files", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["result"]["updated"] == 1
    assert response.json()["result"]["approved"] == 0
    assert response.json()["result"]["denied"] == 0


def test_complete_pending_400(test_client, requests_mocker, mock_src_dest_folder, mock_user, mock_project):
    FILE_DATA_2 = FILE_DATA.copy()
    FILE_DATA_2["global_entity_id"] = "approval_test_geid3"

    # entity_geids file
    mock_data = {"result": [FILE_DATA_2]}
    requests_mocker.post(ConfigClass.NEO4J_SERVICE + "nodes/query/geids", json=mock_data)

    # mock notification
    requests_mocker.post(ConfigClass.EMAIL_SERVICE, json={})

    # mock get file list
    mock_data = {
        "results": [FILE_DATA_2]
    }
    requests_mocker.post(ConfigClass.NEO4J_SERVICE_V2 + "relations/query", json=mock_data)

    # mock get project admins
    mock_data = [{
        "start_node": USER_DATA,
        "end_node": {},
    }]
    requests_mocker.post(ConfigClass.NEO4J_SERVICE + "relations/query", json=mock_data)

    payload = {
        "entity_geids": [FILE_DATA_2["global_entity_id"]],
        "destination_geid": "dest_folder_geid",
        "source_geid": "src_folder_geid",
        "note": "testing",
        "submitted_by": "admin",
    }
    response = test_client.post("/v1/request/copy/approval_fake_project", json=payload)
    assert response.status_code == 200
    assert response.json()["result"]["destination_geid"] == "dest_folder_geid"
    assert response.json()["result"]["note"] == "testing"

    request_obj = response.json()["result"]

    payload = {
        "request_id": request_obj["id"],
        "session_id": "admin-123",
        "status": "complete",
        "review_notes": "done",
        "username": "admin",
    }
    response = test_client.put("/v1/request/copy/approval_fake_project", json=payload)
    assert response.status_code == 400
    assert response.json()["result"]["status"] == "pending"
    assert response.json()["result"]["pending_count"] == 1


def test_pending_files_list_200(test_client, requests_mocker):
    # entity_geids file
    mock_data = {"result": [FILE_DATA]}
    requests_mocker.post(ConfigClass.NEO4J_SERVICE + "nodes/query/geids", json=mock_data)

    payload = {
        "status": "pending"
    }
    response = test_client.get("/v1/request/copy/approval_fake_project", params=payload)
    request_obj = response.json()["result"][0]

    payload = {
        "request_id": request_obj["id"],
    }
    response = test_client.get("/v1/request/copy/approval_fake_project/pending-files", params=payload)

    assert response.status_code == 200
    assert response.json()["result"]["pending_entities"] == ['approval_test_geid3']
    assert response.json()["result"]["pending_count"] == 1
