import logging
import os

from fastapi import APIRouter, FastAPI, HTTPException, Request, UploadFile, File, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from chacra.database import get_db
from chacra.models import Binary, Project, Repo
from chacra.routers.util import repository_is_automatic
from chacra import util


logger = logging.getLogger(__name__)

class Arch(BaseModel):
    arch: str
    project_id: int
    distro: str
    distro_version: str
    ref: str
    sha1: str

app = FastAPI()

router = APIRouter(
    prefix='/binaries/archs',
    responses={405: {'description': 'Method not allowed'}}
)

@router.post('/')
async def index():
    return HTMLResponse(status_code=405)

@router.head('/')
async def index_head(arch: Arch, db: Session = Depends(get_db)):
    binaries = db.query(Binary).filter_by(
        distro=arch.distro,
        distro_version=arch.distro_version,
        ref=arch.ref,
        sha1=arch.sha1,
        arch=arch.arch).all()

    if not binaries:
        raise HTTPException(status_code=404)
    return {}

@router.get('/')
async def index_get(arch: Arch, db: Session = Depends(get_db)):
    binaries = db.query(Binary).filter_by(
        distro=arch.distro,
        distro_version=arch.distro_version,
        ref=arch.ref,
        sha1=arch.sha1,
        arch=arch.arch).all()

    if not binaries:
        raise HTTPException(status_code=404)

    resp = {}
    for b in binaries:
        resp[b.name] = b
    return resp

def get_binary(db: Session, arch: Arch, name: str):
    return db.query(Binary).filter_by(
        name=name, project_id=arch.project_id, arch=arch.arch,
        distro=arch.distro, distro_version=arch.distro_version,
        ref=arch.ref, sha1=arch.sha1
    ).first()

@router.post('/upload')
async def index_post(arch: Arch, request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = await file.read()
    filename = file.filename
    binary = get_binary(db, arch, filename)

    if binary is not None:
        if os.path.exists(binary.path):
            force = request.query_params.get('force', 'false').lower() == 'true'
            if not force:
                raise HTTPException(status_code=400, detail='Resource already exists and "force" key was not used')

    full_path = save_file(arch, contents, filename)

    if binary is None:
        binary = Binary(
            name=filename, project_id=arch.project_id, arch=arch.arch,
            distro=arch.distro, distro_version=arch.distro_version,
            ref=arch.ref, sha1=arch.sha1, path=full_path, size=os.path.getsize(full_path)
        )
        db.add(binary)
    else:
        binary.path = full_path

    db.commit()
    mark_related_repos(arch, db)
    return {}

def mark_related_repos(arch: Arch, db: Session):
    related_projects = util.get_related_projects(arch.project_id)
    repos = []
    projects = []
    for project_name, refs in related_projects.items():
        p = db.query(Project).filter_by(name=project_name).first()
        if not p:
            p = Project(name=project_name)
            db.add(p)
            db.commit()
        projects.append(p)
        repo_query = []
        if refs == ['all']:
            repo_query = db.query(Repo).filter_by(project_id=p.id).all()
        else:
            for ref in refs:
                repo_query.extend(db.query(Repo).filter_by(project_id=p.id, ref=ref).all())
        repos.extend(repo_query)

    if not repos:
        for project in projects:
            repo = Repo(
                project_id=project.id,
                ref=arch.ref,
                distro=arch.distro,
                distro_version=arch.distro_version,
                sha1=arch.sha1,
            )
            repo.needs_update = repository_is_automatic(project.name)
            repo.type = 'binary'  # Assuming a default type, replace with appropriate logic
            db.add(repo)
    else:
        for repo in repos:
            repo.needs_update = repository_is_automatic(repo.project.name)
            if repo.type is None:
                repo.type = 'binary'  # Assuming a default type, replace with appropriate logic

    db.commit()

def create_directory(arch: Arch, filename: str):
    end_part = filename.rstrip('/')
    path = os.path.join(os.getenv('BINARY_ROOT', '/tmp'), end_part.lstrip('/'))
    if not os.path.isdir(path):
        os.makedirs(path)
    return path

def save_file(arch: Arch, contents: bytes, filename: str):
    dir_path = create_directory(arch, filename)
    destination = os.path.join(dir_path, filename)

    with open(destination, 'wb') as f:
        f.write(contents)

    return destination