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

from app.commons.notifier_service.email_service import SrvEmail
from app.commons.neo4j_services import query_node
from app.config import ConfigClass
import requests


def get_user(username: str) -> dict:
    query = {
        "username": username,
        "exact": True,
    }
    response = requests.get(ConfigClass.AUTH_SERVICE + "admin/user", params=query)
    if response.status_code != 200:
        raise Exception(f"Error getting user {username} from auth service: " + str(response.json()))
    return response.json()["result"]

def notify_project_admins(username: str, project_geid: str, request_timestamp: str):
    user_node = get_user(username)

    project_node = query_node("Container", {"global_entity_id": project_geid})
    project_code = project_node["code"]

    payload = {
        "role_names": [f"{project_code}-admin"],
        "status": "active",
    }
    response = requests.post(ConfigClass.AUTH_SERVICE + "admin/roles/users", json=payload)
    project_admins = response.json()["result"]

    for project_admin in project_admins:
        email_service = SrvEmail()
        email_service.send(
            "A new request to copy data to Core needs your approval",
            project_admin["email"],
            ConfigClass.EMAIL_SUPPORT,
            msg_type="html",
            template="copy_request/new_request.html",
            template_kwargs={
                "admin_first_name": project_admin.get("first_name", project_admin["username"]),
                "user_first_name": user_node.get("first_name", user_node["username"]),
                "user_last_name": user_node.get("last_name"),
                "project_name": project_node["name"],
                "request_timestamp": request_timestamp,
            },
        )

def notify_user(username: str, admin_username: str, project_geid: str, request_timestamp: str, complete_timestamp: str):
    user_node = get_user(username)
    admin_node = get_user(admin_username)
    project_node = query_node("Container", {"global_entity_id": project_geid})
    email_service = SrvEmail()
    email_service.send(
        "Your request to copy data to Core is Completed",
        user_node["email"],
        ConfigClass.EMAIL_SUPPORT,
        msg_type="html",
        template="copy_request/complete_request.html",
        template_kwargs={
            "user_first_name": user_node.get("first_name", user_node["username"]),
            "admin_first_name": admin_node.get("first_name", admin_node["username"]),
            "admin_last_name": admin_node.get("last_name"),
            "request_timestamp": request_timestamp,
            "complete_timestamp": complete_timestamp,
            "project_name": project_node["name"],
        },
    )
