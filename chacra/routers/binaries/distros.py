from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from chacra.database import get_db
from chacra import models, util
from chacra.routers.util import repository_is_automatic


class DistroVersion(BaseModel):
    distro_version: str

class Distro(BaseModel):
    distro_name: str

router = APIRouter(
    prefix='/binaries/distros',
    responses={405: {'description': 'Method not allowed'}}
)

@router.get('/{distro_name}/{distro_version}', response_model=dict)
async def get_distro_version(distro_name: str, distro_version: str, request: Request, db: Session = Depends(get_db)):
    project_id = request.state.project_id
    ref = request.state.ref
    sha1 = request.state.sha1

    project = db.query(models.Project).get(project_id)
    if not project or distro_version not in project.distro_versions:
        raise HTTPException(status_code=404)

    resp = {}
    for arch in project.archs:
        binaries = db.query(models.Binary).filter_by(
            project=project,
            distro_version=distro_version,
            distro=distro_name,
            ref=ref,
            sha1=sha1,
            arch=arch).all()
        if binaries:
            resp[arch] = list(set(b.name for b in binaries))
    return resp

@router.post('/{distro_name}/{distro_version}')
async def post_distro_version():
    raise HTTPException(status_code=405, detail='POST requests to this URL are not allowed')

@router.get('/{distro_name}', response_model=dict)
async def get_distro(distro_name: str, request: Request, db: Session = Depends(get_db)):
    project_id = request.state.project_id
    ref = request.state.ref
    sha1 = request.state.sha1

    project = db.query(models.Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404)

    resp = {}
    binaries = db.query(models.Binary).filter_by(
        project=project,
        distro=distro_name,
        ref=ref,
        sha1=sha1).all()

    if not binaries:
        raise HTTPException(status_code=404)

    distro_versions = set(b.distro_version for b in binaries)
    for distro_version in distro_versions:
        resp[distro_version] = list(set(b.arch for b in binaries if b.distro_version == distro_version))
    if not resp:
        raise HTTPException(status_code=404)
    return resp

@router.post('/{distro_name}')
async def post_distro():
    raise HTTPException(status_code=405, detail='POST requests to this URL are not allowed')