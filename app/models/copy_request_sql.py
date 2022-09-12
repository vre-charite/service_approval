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
from sqlalchemy import Column, String, Date, DateTime, Integer, Boolean, ForeignKey, BigInteger
from sqlalchemy.sql.schema import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.config import ConfigClass
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from uuid import uuid4

Base = declarative_base()

class RequestModel(Base):
    __tablename__ = "approval_request"
    __table_args__ = {"schema": ConfigClass.RDS_SCHEMA_DEFAULT}
    id = Column(UUID(as_uuid=True), unique=True, primary_key=True, default=uuid4)
    status = Column(String())
    submitted_by = Column(String())
    submitted_at = Column(DateTime(), default=datetime.utcnow)
    destination_geid = Column(String())
    source_geid = Column(String())
    note = Column(String())
    project_geid = Column(String())
    destination_path = Column(String())
    source_path = Column(String())
    review_notes = Column(String())
    completed_by = Column(String())
    completed_at = Column(DateTime())

    def to_dict(self):
        result = {}
        for field in self.__table__.columns.keys():
            if field in ["submitted_at", "completed_at"]:
                if getattr(self, field):
                    result[field] = str(getattr(self, field).isoformat()[:-3] + 'Z')
                else:
                    result[field] = None
            elif field == "id":
                result[field] = str(getattr(self, field))
            else:
                result[field] = getattr(self, field)
        return result


class EntityModel(Base):
    __tablename__ = "approval_entity"
    __table_args__ = {"schema": ConfigClass.RDS_SCHEMA_DEFAULT}
    id = Column(UUID(as_uuid=True), unique=True, primary_key=True, default=uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey(RequestModel.id))
    entity_geid = Column(String())
    entity_type = Column(String())
    review_status = Column(String())
    reviewed_by = Column(String())
    reviewed_at = Column(String())
    parent_geid = Column(String())
    copy_status = Column(String())
    name = Column(String())
    uploaded_by = Column(String(), nullable=True)
    dcm_id = Column(String(), nullable=True)
    uploaded_at = Column(DateTime(), default=datetime.utcnow)
    file_size = Column(BigInteger(), nullable=True)

    def to_dict(self):
        result = {}
        for field in self.__table__.columns.keys():
            if field == "uploaded_at":
                result[field] = str(getattr(self, field).isoformat()[:-3] + 'Z')
            elif field in ["id", "request_id"]:
                result[field] = str(getattr(self, field))
            else:
                result[field] = getattr(self, field)
        return result

