from app.commons.notifier_service.email_service import SrvEmail
from app.commons.neo4j_services import query_node
from app.config import ConfigClass
import requests


def notify_project_admins(username: str, project_geid: str, request_timestamp: str):
    user_node = query_node("User", {"username": username})
    project_node = query_node("Container", {"global_entity_id": project_geid})
    query_data = {
        "label": "admin",
        "start_label": "User",
        "end_label": "Container",
        "start_params": {
            "status": "active",
        },
        "end_params": {
            "global_entity_id": project_geid,
        },
    }
    response = requests.post(ConfigClass.NEO4J_SERVICE + "relations/query", json=query_data)
    if response.status_code != 200:
        error_msg = f"Error calling Neo4j service: {response.content}"
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    project_admins = [i["start_node"] for i in response.json()]
    for project_admin in project_admins:
        email_service = SrvEmail()
        email_service.send(
            "A new request to copy data to the VRE Core needs your approval",
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
    user_node = query_node("User", {"username": username})
    admin_node = query_node("User", {"username": admin_username})
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
