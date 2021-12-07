from fastapi import APIRouter
from app.config import ConfigClass

router = APIRouter()

## root api, for debuging
@router.get("/")
async def root():
    '''
    For testing if service's up
    '''
    return {"message": "Service Approval On, Version: " + ConfigClass.version}
