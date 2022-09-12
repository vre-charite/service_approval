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

FROM python:3.9-buster

ARG pip_username
ARG pip_password

WORKDIR /usr/src/app
RUN apt-get update && \
    apt-get install -y vim && \
    apt-get install -y less
COPY requirements.txt ./
COPY internal_requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN PIP_USERNAME=$pip_username PIP_PASSWORD=$pip_password pip install --no-cache-dir -r internal_requirements.txt
COPY . .
RUN chmod +x gunicorn_starter.sh

CMD ["python", "run.py"]
