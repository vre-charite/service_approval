from fastapi import FastAPI
from .routers import api_root
from .routers.v1.api_copy_request import api_copy_request

def api_registry(app: FastAPI):
    app.include_router(api_root.router, prefix="/v1")
    app.include_router(api_copy_request.router, prefix="/v1")
