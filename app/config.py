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

import os
from functools import lru_cache
from typing import Any
from typing import Dict
from typing import Optional

from common import VaultClient
from pydantic import BaseSettings
from pydantic import Extra


class VaultConfig(BaseSettings):
    """Store vault related configuration."""

    APP_NAME: str = 'service_approval'
    CONFIG_CENTER_ENABLED: bool = False

    VAULT_URL: Optional[str]
    VAULT_CRT: Optional[str]
    VAULT_TOKEN: Optional[str]

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


def load_vault_settings(settings: BaseSettings) -> Dict[str, Any]:
    config = VaultConfig()

    if not config.CONFIG_CENTER_ENABLED:
        return {}

    client = VaultClient(config.VAULT_URL, config.VAULT_CRT, config.VAULT_TOKEN)
    return client.get_from_vault(config.APP_NAME)


class Settings(BaseSettings):
    env: str = os.environ.get('env')
    version: str = "0.1.0"

    port: int = 8000
    host: str = "0.0.0.0"

    AUTH_SERVICE: str
    NEO4J_SERVICE: str
    DATA_OPS_UTIL: str
    EMAIL_SERVICE: str
    UTILITY_SERVICE: str

    RDS_SCHEMA_DEFAULT: str
    RDS_DB_URI: str

    EMAIL_SUPPORT: str = "jzhang@indocresearch.org"

    CORE_ZONE_LABEL: str
    GREEN_ZONE_LABEL: str

    def __init__(self, *args: Any, **kwds: Any) -> None:
        super().__init__(*args, **kwds)

        self.AUTH_SERVICE = self.AUTH_SERVICE + "/v1/"
        NEO4J_HOST = self.NEO4J_SERVICE
        self.NEO4J_SERVICE = NEO4J_HOST + "/v1/neo4j/"
        self.NEO4J_SERVICE_V2 = NEO4J_HOST + "/v2/neo4j/"
        self.DATA_UTILITY_SERVICE = self.DATA_OPS_UTIL + "/v1/"
        self.EMAIL_SERVICE = self.EMAIL_SERVICE + "/v1/email"
        self.UTILITY_SERVICE = self.UTILITY_SERVICE + "/v1/"

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = Extra.allow

        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return env_settings, load_vault_settings, init_settings, file_secret_settings


@lru_cache(1)
def get_settings():
    settings = Settings()
    return settings


ConfigClass = get_settings()
