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
from fastapi import FastAPI
from fastapi.testclient import TestClient
from run import app
from app.config import ConfigClass
from app.resources.helpers import get_geid
import os

class SetUpTest:
    object_id_list = []
    def __init__(self, log):
        self.log = log
        self.app = self.create_test_client()

    def create_test_client(self):
        client = TestClient(app)
        return client

    def add_user_to_project(self, user_id, project_id, role):
        payload = {
            "start_id": user_id,
            "end_id": project_id,
        }
        response = requests.post(ConfigClass.NEO4J_SERVICE + f"relations/{role}", json=payload)
        if response.status_code != 200:
            raise Exception(f"Error adding user to project: {response.json()}")

    def remove_user_from_project(self, user_id, project_id):
        payload = {
            "start_id": user_id,
            "end_id": project_id,
        }
        response = requests.delete(ConfigClass.NEO4J_SERVICE + "relations", params=payload)
        if response.status_code != 200:
            raise Exception(f"Error removing user from project: {response.json()}")

    def create_test_project_with_data(self, project_name):
        '''
        The structure will be:
        Project_<time>
            |--- File 1
            |--- Folder 1
                    |--- File 2
        '''

        test_payload = {
            "name": project_name,
            "path": project_name,
            "code": project_name,
            "description": "Project created by unit test, will be deleted soon...",
            "discoverable": 'true',
            "type": "Usecase",
            "tags": ['test'],
            "global_entity_id": get_geid(),
        }

        test_project_node = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/Container", json=test_payload)
        test_project_node = test_project_node.json()[0]

        # create a name folder
        test_payload = {
            "archived":False,
            "display_path":"",
            "folder_level":0,
            "folder_relative_path":"",
            "global_entity_id":get_geid(),
            "list_priority":10,
            "name":"admin",
            "project_code":project_name,
            "uploader":"admin",
            "extra_labels": [ConfigClass.GREEN_ZONE_LABEL]
        }
        test_name_node = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/Folder", json=test_payload)
        test_name_node = test_name_node.json()[0]

        test_payload = {
            "archived":False,
            "display_path":"",
            "folder_level":0,
            "folder_relative_path":"",
            "global_entity_id":get_geid(),
            "list_priority":10,
            "name":"admin",
            "project_code":project_name,
            "uploader":"admin",
            "extra_labels": [ConfigClass.CORE_ZONE_LABEL]
        }
        test_core_name_node = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/Folder", json=test_payload)
        test_core_name_node = test_core_name_node.json()[0]

        # create a folder
        test_payload = {
            "archived":False,
            "display_path":"admin/folder1",
            "folder_level":1,
            "folder_relative_path":"admin",
            "global_entity_id":get_geid(),
            "list_priority":10,
            "name":"folder1",
            "project_code":project_name,
            "uploader":"admin",
            "extra_labels": [ConfigClass.GREEN_ZONE_LABEL]
        }
        test_folder_node = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/Folder", json=test_payload)
        test_folder_node = test_folder_node.json()[0]


        # create two file
        test_payload = {
            "archived":False,
            "display_path":"admin/folder1/file1",
            "file_size": 1,
            "global_entity_id":get_geid(),
            "list_priority": 20,
            "location": "minio://http://127.0.0.1/gr-jun29test/admin/hello123/Android.svg",
            "name": "file1",
            "operator":"admin",
            "project_code": project_name,
            "uploader": "admin",
            "extra_labels": [ConfigClass.GREEN_ZONE_LABEL],
            "parent_folder_geid": test_folder_node["global_entity_id"]
        }
        test_file_node_1 = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/File", json=test_payload)
        test_file_node_1 = test_file_node_1.json()[0]

        test_payload = {
            "archived":False,
            "display_path":"admin/file2",
            "file_size": 1,
            "global_entity_id":get_geid(),
            "list_priority": 10,
            "location": "minio://http://127.0.0.1/gr-jun29test/admin/hello123/Android.svg",
            "name": "file2",
            "operator":"admin",
            "project_code": project_name,
            "uploader": "admin",
            "extra_labels": [ConfigClass.GREEN_ZONE_LABEL],
            "parent_folder_geid": test_name_node["global_entity_id"]
        }
        test_file_node_2 = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/File", json=test_payload)
        test_file_node_2 = test_file_node_2.json()[0]

        # make order as project->folder1->file1->file2
        self.__class__.object_id_list.append(test_project_node.get("id"))
        self.__class__.object_id_list.append(test_name_node.get("id"))
        self.__class__.object_id_list.append(test_folder_node.get("id"))
        self.__class__.object_id_list.append(test_file_node_1.get("id"))
        self.__class__.object_id_list.append(test_file_node_2.get("id"))

        self.__class__.object_id_list.append(test_core_name_node.get("id"))

        print(self.object_id_list)

        # make the relationship
        create_node_url = ConfigClass.NEO4J_SERVICE + 'relations/own'
        new_relation = requests.post(create_node_url, json={
            "start_id":self.object_id_list[1], "end_id":self.object_id_list[4]})
        new_relation = requests.post(create_node_url, json={
            "start_id":self.object_id_list[2], "end_id":self.object_id_list[3]})
        new_relation = requests.post(create_node_url, json={
            "start_id":self.object_id_list[1], "end_id":self.object_id_list[2]})
        new_relation = requests.post(create_node_url, json={
            "start_id":self.object_id_list[0], "end_id":self.object_id_list[1]})

        new_relation = requests.post(create_node_url, json={
            "start_id":self.object_id_list[0], "end_id":self.object_id_list[5]})

        return test_project_node, \
            [
                test_folder_node,
                test_name_node,
                test_core_name_node,
                test_file_node_1,
                test_file_node_2
            ]

    def delete_node(self, label, node_id):
        res = requests.delete(ConfigClass.NEO4J_SERVICE + f"nodes/{label}/node/{node_id}")
        if res.status_code != 200:
            raise Exception(f"Error removing {label}: {res.json()}")


if __name__ == '__main__':
    log="log"
    st = SetUpTest(log=log)
    st.create_folder("unittest")
