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

from app.config import ConfigClass
import requests
import json


class SrvEmail():
    def send(self, subject, receiver, sender, content="", msg_type="plain", template=None, template_kwargs={}):
        url = ConfigClass.EMAIL_SERVICE
        payload = {
            "subject": subject,
            "sender": sender,
            "receiver": [receiver],
            "msg_type": msg_type,
        }
        if content:
            payload["message"] = content
        if template:
            payload["template"] = template
            payload["template_kwargs"] = template_kwargs
        res = requests.post(
            url=url,
            json=payload
        )
        return res.json()
