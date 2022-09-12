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

from fastapi_sqlalchemy import db
from app.models.copy_request_sql import EntityModel, RequestModel
from datetime import datetime


def get_sql_files_recursive(request_id: str, folder_geid: str, file_geids: list[str] = None) -> list[EntityModel]:
    if not file_geids:
        file_geids = []

    entities = db.session.query(EntityModel).filter_by(request_id=request_id, parent_geid=folder_geid)
    for entity in entities:
        if entity.entity_type == "file":
            if entity.review_status == "pending":
                file_geids.append(entity.entity_geid)
        else:
            file_geids = get_sql_files_recursive(request_id, entity.entity_geid, file_geids=file_geids)
    return file_geids


def get_all_sub_files(request_id: str, entity_geids: list[str]) -> list[str]:
    entities = db.session.query(EntityModel).filter_by(request_id=request_id).filter(
        EntityModel.entity_geid.in_(entity_geids)
    )
    file_geids = []
    for entity in entities:
        if entity.entity_type == "file":
            file_geids.append(entity.entity_geid)
        else:
            # Get all files in subfolder
            file_geids = get_sql_files_recursive(request_id, entity.entity_geid, file_geids=file_geids)
    return file_geids


def get_sql_file_nodes_recursive(request_id: str, folder_geid: str, review_status: str, files: list=None) -> list[EntityModel]:
    if not files:
        files = []

    entities = db.session.query(EntityModel).filter_by(request_id=request_id, parent_geid=folder_geid)
    for entity in entities:
        if entity.entity_type == "file":
            if entity.review_status == review_status:
                files.append(entity.entity_geid)
        else:
            files = get_sql_file_nodes_recursive(request_id, entity.entity_geid, review_status, files=files)
    return files


def get_all_sub_folder_nodes(request_id: str, entity_geids: list[str], review_status: str) -> list[str]:
    entities = db.session.query(EntityModel).filter_by(request_id=request_id).filter(
        EntityModel.entity_geid.in_(entity_geids)
    )
    files = []
    for entity in entities:
        if entity.entity_type == "folder":
            # Get all files in subfolder
            files = get_sql_file_nodes_recursive(request_id, entity.entity_geid, review_status, files=files)
    return files


def update_files_sql(request_id: str, review_status: str, username: str, file_geids: list[str]) -> int:
    review_data = {
        "review_status": review_status,
        "reviewed_by": username,
        "reviewed_at": datetime.utcnow(),
    }
    files = db.session.query(EntityModel).filter_by(request_id=request_id).filter(
        EntityModel.entity_geid.in_(file_geids)
    )
    files.update(review_data)
    db.session.commit()
    return files.count()


def create_entity_from_node(request_id: str, entity: dict) -> EntityModel:
    # Create entity in psql given neo4j node
    if "File" in entity["labels"]:
        entity_type = "file"
    else:
        entity_type = "folder"

    entity_data = {
        "request_id": request_id,
        "entity_geid": entity["global_entity_id"],
        "entity_type": entity_type,
        "parent_geid": entity["parent_folder_geid"],
        "name": entity["name"],
        "uploaded_by": entity["uploader"],
        "uploaded_at": entity["time_created"],
        "dcm_id": entity.get("dcm_id"),
    }
    if entity_type == "file":
        entity_data["review_status"] = "pending"
        entity_data["file_size"] = entity["file_size"]
        entity_data["copy_status"] = "pending"
    entity_obj = EntityModel(**entity_data)
    db.session.add(entity_obj)
    db.session.commit()
    return entity_obj
