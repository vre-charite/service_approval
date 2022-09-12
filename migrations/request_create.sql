// Copyright 2022 Indoc Research
// 
// Licensed under the EUPL, Version 1.2 or – as soon they
// will be approved by the European Commission - subsequent
// versions of the EUPL (the "Licence");
// You may not use this work except in compliance with the
// Licence.
// You may obtain a copy of the Licence at:
// 
// https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12
// 
// Unless required by applicable law or agreed to in
// writing, software distributed under the Licence is
// distributed on an "AS IS" basis,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
// express or implied.
// See the Licence for the specific language governing
// permissions and limitations under the Licence.
// 

CREATE TABLE indoc_vre.approval_request (
	id UUID NOT NULL, 
	status VARCHAR, 
	submitted_by VARCHAR, 
	submitted_at TIMESTAMP WITHOUT TIME ZONE, 
	destination_geid VARCHAR, 
	source_geid VARCHAR, 
	note VARCHAR, 
	project_geid VARCHAR, 
	destination_path VARCHAR, 
	source_path VARCHAR, 
	review_notes VARCHAR, 
	completed_by VARCHAR, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (id)
);

CREATE TABLE indoc_vre.approval_entity (
	id UUID NOT NULL, 
	request_id UUID, 
	entity_geid VARCHAR, 
	entity_type VARCHAR, 
	review_status VARCHAR, 
	reviewed_by VARCHAR, 
	reviewed_at VARCHAR, 
	parent_geid VARCHAR, 
	copy_status VARCHAR, 
	name VARCHAR, 
	uploaded_by VARCHAR, 
	dcm_id VARCHAR, 
	uploaded_at TIMESTAMP WITHOUT TIME ZONE, 
	file_size BIGINT, 
	PRIMARY KEY (id), 
	UNIQUE (id), 
	FOREIGN KEY(request_id) REFERENCES indoc_vre.approval_request (id)
);
