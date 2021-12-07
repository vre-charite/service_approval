import math

from fastapi import APIRouter, Depends, Request
from fastapi_sqlalchemy import db
from fastapi_utils import cbv

from app.commons.logger_services.logger_factory_service import SrvLoggerFactory
from app.commons.neo4j_services import bulk_get_by_geids, get_files_recursive, get_node_by_geid
from app.commons.psql_services import create_entity_from_node, get_all_sub_files, update_files_sql
from app.commons.pipeline_ops.copy import trigger_copy_pipeline
from app.models.base import APIResponse, EAPIResponseCode
from app.models.copy_request import (GETRequest, GETRequestFiles, GETRequestFilesResponse, GETRequestResponse,
                                     PATCHRequestFiles, POSTRequest, POSTRequestResponse, PUTRequest, PUTRequestFiles,
                                     PUTRequestFilesResponse, GETPendingResponse, GETRequestPending)
from app.models.copy_request_sql import EntityModel, RequestModel
from datetime import datetime
from .request_notify import notify_project_admins, notify_user


logger = SrvLoggerFactory("api_copy_request").get_logger()

router = APIRouter()
_API_TAG = "CopyRequest"
_API_NAMESPACE = "copy_request"


@cbv.cbv(router)
class APICopyRequest:

    @router.post("/request/copy/{project_geid}", tags=[_API_TAG], response_model=POSTRequestResponse,
            summary="Create a copy request")
    def create_request(self, project_geid: str, data: POSTRequest):
        logger.info("Create Request called")
        api_response = APIResponse()

        dest_folder_node = get_node_by_geid(data.destination_geid)
        source_folder_node = get_node_by_geid(data.source_geid)
        request_data = {
            "status": "pending",
            "submitted_by": data.submitted_by,
            "destination_geid": data.destination_geid,
            "source_geid": data.source_geid,
            "note": data.note,
            "project_geid": project_geid,
            "destination_path": dest_folder_node["display_path"],
            "source_path": source_folder_node["display_path"],
        }
        request_obj = RequestModel(**request_data)
        db.session.add(request_obj)
        db.session.commit()
        db.session.refresh(request_obj)

        all_files = []
        entities = bulk_get_by_geids(data.entity_geids)
        for entity in entities:
            if "File" in entity["labels"]:
                # Top level files in request need a parent_folder_geid of None
                entity["parent_folder_geid"] = None
                all_files.append(entity)
            else:
                # Top level files in request need a parent_folder_geid of None
                entity["parent_folder_geid"] = None
                all_files.append(entity)
                all_files = get_files_recursive(entity["global_entity_id"], all_files=all_files)

        for entity in all_files:
            create_entity_from_node(request_obj.id, entity)

        submitted_at = request_obj.submitted_at.strftime("%Y-%m-%d %H:%M:%S")
        notify_project_admins(data.submitted_by, project_geid, submitted_at)
        api_response.result = request_obj.to_dict()
        return api_response.json_response()

    @router.get("/request/copy/{project_geid}", tags=[_API_TAG], response_model=GETRequestResponse,
            summary="Create a copy request")
    def list_requests(self, project_geid: str, params: GETRequest = Depends(GETRequest)):
        logger.info("List Requests called")
        api_response = APIResponse()
        results = db.session.query(RequestModel).filter_by(
            status=params.status,
            project_geid=project_geid,
        )
        if params.submitted_by:
            results = results.filter_by(submitted_by=params.submitted_by)
        results = results.order_by(RequestModel.submitted_at.desc()).limit(params.page_size).offset(params.page * params.page_size)

        if params.submitted_by:
            total = db.session.query(RequestModel).filter_by(
                status=params.status,
                project_geid=project_geid,
                submitted_by=params.submitted_by
            ).count()
        else:
            total = db.session.query(RequestModel).filter_by(
                status=params.status,
                project_geid=project_geid,
            ).count()
        api_response.result = [i.to_dict() for i in results]
        api_response.total = total
        api_response.page = params.page
        api_response.num_of_pages = math.ceil(total / params.page_size)
        return api_response.json_response()

    @router.get("/request/copy/{project_geid}/files", tags=[_API_TAG], response_model=GETRequestFilesResponse,
            summary="List request files")
    def list_request_files(self, project_geid: str, params: GETRequestFiles = Depends(GETRequestFiles)):
        logger.info("List request files called")
        api_response = APIResponse()
        query_params = {
            "request_id": params.request_id
        }
        if params.parent_geid:
            query_params["parent_geid"] = params.parent_geid
        else:
            query_params["parent_geid"] = None

        sql_query = db.session.query(EntityModel)
        for key, value in params.query.items():
            if key in params.partial:
                sql_query = sql_query.filter(getattr(EntityModel, key).contains(value))
            else:
                query_params[key] = value

        if params.order_type == "desc":
            order_by = getattr(EntityModel, params.order_by).desc()
        else:
            order_by = getattr(EntityModel, params.order_by).asc()
        sql_query = sql_query.filter_by(**query_params).order_by(EntityModel.entity_type.desc(), order_by)

        results = sql_query.limit(params.page_size).offset(params.page * params.page_size)
        routing = []
        if params.parent_geid:
            entity_geid = params.parent_geid
            while entity_geid:
                file = db.session.query(EntityModel).filter_by(entity_geid=entity_geid).first()
                routing.append(file.to_dict())
                entity_geid = file.parent_geid

        total = db.session.query(EntityModel).filter_by(**query_params).count()
        api_response.result = {"data": [i.to_dict() for i in results], "routing": routing}
        api_response.total = total
        api_response.page = params.page
        api_response.num_of_pages = math.ceil(total / params.page_size)
        return api_response.json_response()

    @router.put("/request/copy/{project_geid}/files", tags=[_API_TAG], response_model=PUTRequestFilesResponse,
            summary="Approve all files and trigger copy pipeline")
    def review_all_files(self, project_geid: str, data: PUTRequestFiles, request: Request):
        logger.info("Review all files called")
        api_response = APIResponse()
        review_status = data.review_status

        approved = db.session.query(EntityModel).filter_by(request_id=data.request_id, review_status="approved")
        denied = db.session.query(EntityModel).filter_by(request_id=data.request_id, review_status="denied")
        skipped_data = {"approved": approved.count(), "denied": denied.count()}

        file_geids = []
        entities = db.session.query(EntityModel).filter_by(request_id=data.request_id, review_status="pending")
        file_geids = [i.entity_geid for i in entities]
        result = update_files_sql(data.request_id, review_status, data.username, file_geids)

        if review_status == "approved":
            top_level_entities = db.session.query(EntityModel).filter_by(request_id=data.request_id, parent_geid=None)
            top_level_geids = [i.entity_geid for i in top_level_entities]
            if top_level_geids:
                # Send top level file/folder geids to copy pipeline
                logger.info(f"Triggering pipeline for {top_level_geids}")
                request_obj = db.session.query(RequestModel).get(data.request_id)
                auth = {
                    "Authorization": request.headers.get("Authorization").replace("Bearer ", ""),
                    "Refresh-Token": request.headers.get("Refresh-Token"),
                }
                copy_result = trigger_copy_pipeline(request_obj, top_level_geids, data.username, data.session_id, auth)
                logger.info(f"Pipeline trigger for {len(copy_result)} files")

        skipped_data["updated"] = result
        api_response.result = skipped_data
        return api_response.json_response()

    @router.patch("/request/copy/{project_geid}/files", tags=[_API_TAG], response_model=PUTRequestFilesResponse,
            summary="Approve files and trigger copy pipeline")
    def review_files(self, project_geid: str, data: PATCHRequestFiles, request: Request):
        logger.info("Review files called")
        api_response = APIResponse()
        review_status = data.review_status

        approved = db.session.query(EntityModel).filter_by(request_id=data.request_id, review_status="approved")
        denied = db.session.query(EntityModel).filter_by(request_id=data.request_id, review_status="denied")
        skipped_data = {"approved": approved.count(), "denied": denied.count()}

        file_geids = get_all_sub_files(data.request_id, data.entity_geids)
        result = update_files_sql(data.request_id, review_status, data.username, file_geids)

        if review_status == "approved":
            if data.entity_geids:
                # Send geid's of file/folders submitted by frontend to copy pipeline
                logger.info(f"Triggering pipeline for {data.entity_geids}")
                request_obj = db.session.query(RequestModel).get(data.request_id)
                auth = {
                    "Authorization": request.headers.get("Authorization").replace("Bearer ", ""),
                    "Refresh-Token": request.headers.get("Refresh-Token"),
                }
                copy_result = trigger_copy_pipeline(
                    request_obj,
                    data.entity_geids,
                    data.username,
                    data.session_id,
                    auth
                )
                logger.info(f"Pipeline trigger for {len(copy_result)} files")
        skipped_data["updated"] = result
        api_response.result = skipped_data
        return api_response.json_response()

    @router.put("/request/copy/{project_geid}", tags=[_API_TAG], response_model=PUTRequestFilesResponse,
            summary="Approve files")
    def complete_request(self, project_geid: str, data: PUTRequest):
        logger.info("Complete request called")
        api_response = APIResponse()

        request_obj = db.session.query(RequestModel).get(data.request_id)

        query_params = {
            "request_id": data.request_id,
            "review_status": "pending",
        }
        pending_files = db.session.query(EntityModel).filter_by(**query_params)
        if pending_files.count():
            pending_entities = [i.entity_geid for i in pending_files]
            # exclude delted files from pending list
            pending_nodes = bulk_get_by_geids(pending_entities)
            for entity in pending_nodes:
                if entity["archived"]:
                    pending_entities.remove(entity["global_entity_id"])
            if pending_entities:
                error_msg = f"{len(pending_entities)} pending files in request"
                logger.info(error_msg)
                api_response.error_msg = error_msg
                api_response.result = {
                    "status": "pending",
                    "pending_entities": pending_entities,
                    "pending_count": len(pending_entities),
                }
                api_response.code = EAPIResponseCode.bad_request
                return api_response.json_response()

        request_obj.status = data.status
        request_obj.review_notes = data.review_notes
        request_obj.completed_by = data.username
        request_obj.completed_at = datetime.utcnow()
        db.session.commit()
        db.session.refresh(request_obj)

        submitted_at = request_obj.submitted_at.strftime("%Y-%m-%d %H:%M:%S")
        completed_at = request_obj.completed_at.strftime("%Y-%m-%d %H:%M:%S")
        notify_user(request_obj.submitted_by, data.username, project_geid, submitted_at, completed_at)
        api_response.result = {
            "status": data.status,
            "pending_entities": [],
            "pending_count": 0,
        }
        return api_response.json_response()

    @router.get("/request/copy/{project_geid}/pending-files", tags=[_API_TAG], response_model=GETPendingResponse,
            summary="Get pending count")
    def get_pending(self, project_geid: str, params: GETRequestPending = Depends(GETRequestPending)):
        logger.info("Get Pending called")
        api_response = APIResponse()

        request_obj = db.session.query(RequestModel).get(params.request_id)

        query_params = {
            "request_id": params.request_id,
            "review_status": "pending",
        }
        pending_files = db.session.query(EntityModel).filter_by(**query_params)
        logger.info(f"{pending_files.count()} pending files in request")
        pending_entities = [i.entity_geid for i in pending_files]
        if pending_entities:
            # exclude deleted files from pending list
            pending_nodes = bulk_get_by_geids(pending_entities)
            for entity in pending_nodes:
                if entity["archived"]:
                    pending_entities.remove(entity["global_entity_id"])
        api_response.result = {
            "pending_entities": pending_entities,
            "pending_count": len(pending_entities),
        }
        return api_response.json_response()

    @router.delete("/request/copy/{project_geid}/delete/{request_id}", tags=[_API_TAG], summary="Delete Request")
    def delete_request(self, project_geid: str, request_id: str):
        api_response = APIResponse()
        request_files = db.session.query(EntityModel).filter_by(request_id=request_id)
        for request_file in request_files:
            db.session.delete(request_file)
        db.session.commit()

        request_obj = db.session.query(RequestModel).get(request_id)
        db.session.delete(request_obj)
        db.session.commit()
        api_response.result = "success"
        return api_response.json_response()

