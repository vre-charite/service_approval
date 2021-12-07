import unittest
import mock
from tests.logger import Logger
from tests.prepare_test import SetUpTest
from app.commons.neo4j_services import query_node
from app.routers.v1.api_copy_request.request_notify import notify_project_admins
from app.models.copy_request_sql import RequestModel

class TestCopyApporval(unittest.TestCase):
    log = Logger(name="test_copy_approval.log")
    test = SetUpTest(log)
    project_code = "unittest_copy_approval"
    request_ids = []

    @classmethod
    def setUpClass(cls):
        cls.log = cls.test.log
        cls.app = cls.test.app
        cls.project, cls.file_list = cls.test.create_test_project_with_data(cls.project_code)
        cls.project_geid = cls.project["global_entity_id"]
        cls.greenroom_name_folder = query_node("Folder", {"name": "admin", "project_code": cls.project_code})
        cls.core_name_folder = query_node("Folder", {"name": "admin", "project_code": cls.project_code})

    @classmethod
    def tearDownClass(cls):
        cls.test.delete_node("Container", cls.project["id"])
        for entity in cls.file_list:
            if "File" in entity["labels"]:
                cls.test.delete_node("File", entity["id"])
            elif "Folder" in entity["labels"]:
                cls.test.delete_node("Folder", entity["id"])
        for request_id in cls.request_ids:
            cls.app.delete(f"/v1/request/copy/{cls.project_geid}/delete/{request_id}")

    @mock.patch("app.routers.v1.api_copy_request.request_notify.notify_project_admins")
    def test_01_create_request(self, mock_func):
        mock_func.return_value = None

        folder_node = query_node("Folder", {"display_path": "admin/folder1", "project_code": self.project_code})
        file_node = query_node("File", {"display_path": "admin/file2", "project_code": self.project_code})
        payload = {
            "entity_geids": [folder_node["global_entity_id"], file_node["global_entity_id"]],
            "destination_geid": self.core_name_folder["global_entity_id"],
            "source_geid": self.greenroom_name_folder["global_entity_id"],
            "note": "testing",
            "submitted_by": "admin",
        }
        response = self.app.post(f"/v1/request/copy/{self.project_geid}", json=payload)
        self.assertEqual(response.status_code, 200)
        self.request_ids.append(response.json()["result"]["id"])
        self.assertEqual(response.json()["result"]["destination_geid"], self.core_name_folder["global_entity_id"])
        self.assertEqual(response.json()["result"]["note"], "testing")

    def test_02_list_requests(self):
        payload = {
            "status": "pending"
        }
        response = self.app.get(f"/v1/request/copy/{self.project_geid}", params=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"][0]["destination_geid"], self.core_name_folder["global_entity_id"])
        self.assertEqual(response.json()["result"][0]["note"], "testing")

    def test_03_list_request_files(self):
        payload = {
            "status": "pending"
        }
        response = self.app.get(f"/v1/request/copy/{self.project_geid}", params=payload)
        request_obj = response.json()["result"][0]

        payload = {
            "request_id": request_obj["id"],
            "order_by": "name",
            "order_type": "desc",
        }
        response = self.app.get(f"/v1/request/copy/{self.project_geid}/files", params=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["result"]["data"]), 2)
        self.assertEqual(len(response.json()["result"]["routing"]), 0)
        self.assertEqual(response.json()["result"]["data"][0]["name"], "folder1")
        self.assertEqual(response.json()["result"]["data"][1]["name"], "file2")

        payload = {
            "request_id": request_obj["id"],
            "order_by": "name",
            "order_type": "asc",
        }
        response = self.app.get(f"/v1/request/copy/{self.project_geid}/files", params=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"]["data"][1]["name"], "folder1")
        self.assertEqual(response.json()["result"]["data"][0]["name"], "file2")

    @mock.patch("app.commons.pipeline_ops.copy.trigger_copy_pipeline")
    def test_04_approve_partial_files(self, mock_func):
        payload = {
            "status": "pending"
        }
        response = self.app.get(f"/v1/request/copy/{self.project_geid}", params=payload)
        request_obj = response.json()["result"][0]

        payload = {
            "entity_geids": [
                self.file_list[0]["global_entity_id"]
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
        print(self.file_list[0])
        mock_func.return_value = [payload["entity_geids"]]
        response = self.app.patch(f"/v1/request/copy/{self.project_geid}/files", json=payload, headers=headers)
        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"]["updated"], 1)
        self.assertEqual(response.json()["result"]["approved"], 0)
        self.assertEqual(response.json()["result"]["denied"], 0)

    def test_05_list_request_sub_files(self):
        payload = {
            "status": "pending"
        }
        response = self.app.get(f"/v1/request/copy/{self.project_geid}", params=payload)
        request_obj = response.json()["result"][0]

        payload = {
            "request_id": request_obj["id"],
            "parent_geid": self.file_list[0]["global_entity_id"]
        }
        response = self.app.get(f"/v1/request/copy/{self.project_geid}/files", params=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"]["data"][0]["name"], "file1")

    @mock.patch("app.commons.pipeline_ops.copy.trigger_copy_pipeline")
    def test_06_approve_all_files(self, mock_func):
        payload = {
            "status": "pending"
        }
        response = self.app.get(f"/v1/request/copy/{self.project_geid}", params=payload)
        request_obj = response.json()["result"][0]

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
        mock_func.return_value = []
        response = self.app.put(f"/v1/request/copy/{self.project_geid}/files", json=payload, headers=headers)
        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"]["updated"], 1)
        self.assertEqual(response.json()["result"]["approved"], 1)
        self.assertEqual(response.json()["result"]["denied"], 0)

    @mock.patch("app.routers.v1.api_copy_request.request_notify.notify_user")
    def test_07_complete_request(self, mock_func):
        mock_func.return_value = ""
        payload = {
            "status": "pending"
        }
        response = self.app.get(f"/v1/request/copy/{self.project_geid}", params=payload)
        request_obj = response.json()["result"][0]

        payload = {
            "request_id": request_obj["id"],
            "session_id": "admin-123",
            "status": "complete",
            "review_notes": "done",
            "username": "admin",
        }
        response = self.app.put(f"/v1/request/copy/{self.project_geid}", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"]["status"], "complete")
        self.assertEqual(response.json()["result"]["pending_count"], 0)

    @mock.patch("app.routers.v1.api_copy_request.request_notify.notify_project_admins")
    def test_08_create_request_folder_not_found(self, mock_func):
        mock_func.return_value = None

        folder_node = query_node("Folder", {"display_path": "admin/folder1", "project_code": self.project_code})
        file_node = query_node("File", {"display_path": "admin/file2", "project_code": self.project_code})
        payload = {
            "entity_geids": [folder_node["global_entity_id"], file_node["global_entity_id"]],
            "destination_geid": "invalid_approval_test",
            "source_geid": self.greenroom_name_folder["global_entity_id"],
            "note": "testing",
            "submitted_by": "admin",
        }
        response = self.app.post(f"/v1/request/copy/{self.project_geid}", json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error_msg"], "Folder not found")

    @mock.patch("app.routers.v1.api_copy_request.request_notify.notify_project_admins")
    def test_09_create_request_sub_file(self, mock_func):
        mock_func.return_value = None

        file_node = query_node("File", {"display_path": "admin/folder1/file1", "project_code": self.project_code})
        payload = {
            "entity_geids": [file_node["global_entity_id"]],
            "destination_geid": self.core_name_folder["global_entity_id"],
            "source_geid": self.greenroom_name_folder["global_entity_id"],
            "note": "testing",
            "submitted_by": "admin",
        }
        response = self.app.post(f"/v1/request/copy/{self.project_geid}", json=payload)
        self.assertEqual(response.status_code, 200)
        self.request_ids.append(response.json()["result"]["id"])
        self.assertEqual(response.json()["result"]["destination_geid"], self.core_name_folder["global_entity_id"])
        self.assertEqual(response.json()["result"]["note"], "testing")

    def test_10_deny_partial_files(self):
        payload = {
            "status": "pending"
        }
        response = self.app.get(f"/v1/request/copy/{self.project_geid}", params=payload)
        request_obj = response.json()["result"][0]

        payload = {
            "entity_geids": [
                self.file_list[3]["global_entity_id"]
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
        response = self.app.patch(f"/v1/request/copy/{self.project_geid}/files", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"]["updated"], 1)
        self.assertEqual(response.json()["result"]["approved"], 0)
        self.assertEqual(response.json()["result"]["denied"], 0)

    @mock.patch("app.routers.v1.api_copy_request.request_notify.notify_project_admins")
    def test_11_partial_approved(self, mock_func):
        mock_func.return_value = None
        folder_node = query_node("Folder", {"display_path": "admin/folder1", "project_code": self.project_code})
        file_node = query_node("File", {"display_path": "admin/file2", "project_code": self.project_code})
        payload = {
            "entity_geids": [folder_node["global_entity_id"], file_node["global_entity_id"]],
            "destination_geid": self.core_name_folder["global_entity_id"],
            "source_geid": self.greenroom_name_folder["global_entity_id"],
            "note": "testing",
            "submitted_by": "admin",
        }
        response = self.app.post(f"/v1/request/copy/{self.project_geid}", json=payload)
        self.assertEqual(response.status_code, 200)
        self.request_ids.append(response.json()["result"]["id"])
        self.assertEqual(response.json()["result"]["destination_geid"], self.core_name_folder["global_entity_id"])
        self.assertEqual(response.json()["result"]["note"], "testing")

        request_obj = response.json()["result"]

        payload = {
            "entity_geids": [
                self.file_list[3]["global_entity_id"]
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
        response = self.app.patch(f"/v1/request/copy/{self.project_geid}/files", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"]["updated"], 1)
        self.assertEqual(response.json()["result"]["approved"], 0)
        self.assertEqual(response.json()["result"]["denied"], 0)

        payload = {
            "entity_geids": [
                self.file_list[4]["global_entity_id"]
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
        response = self.app.patch(f"/v1/request/copy/{self.project_geid}/files", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"]["updated"], 1)
        self.assertEqual(response.json()["result"]["approved"], 0)
        self.assertEqual(response.json()["result"]["denied"], 1)

    @mock.patch("app.routers.v1.api_copy_request.request_notify.notify_project_admins")
    @mock.patch("app.routers.v1.api_copy_request.request_notify.notify_user")
    def test_12_complete_pending(self, mock_func, mock_users):
        mock_func.return_value = None
        mock_users.return_value = None
        folder_node = query_node("Folder", {"display_path": "admin/folder1", "project_code": self.project_code})
        file_node = query_node("File", {"display_path": "admin/file2", "project_code": self.project_code})
        payload = {
            "entity_geids": [folder_node["global_entity_id"], file_node["global_entity_id"]],
            "destination_geid": self.core_name_folder["global_entity_id"],
            "source_geid": self.greenroom_name_folder["global_entity_id"],
            "note": "testing",
            "submitted_by": "admin",
        }
        response = self.app.post(f"/v1/request/copy/{self.project_geid}", json=payload)
        self.assertEqual(response.status_code, 200)
        self.request_ids.append(response.json()["result"]["id"])
        self.assertEqual(response.json()["result"]["destination_geid"], self.core_name_folder["global_entity_id"])
        self.assertEqual(response.json()["result"]["note"], "testing")

        request_obj = response.json()["result"]

        payload = {
            "request_id": request_obj["id"],
            "session_id": "admin-123",
            "status": "complete",
            "review_notes": "done",
            "username": "admin",
        }
        response = self.app.put(f"/v1/request/copy/{self.project_geid}", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["result"]["status"], "pending")
        self.assertEqual(response.json()["result"]["pending_count"], 2)
