import os
import logging

from fastapi import APIRouter, HTTPException, Request, Depends, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from chacra.database import get_db
from chacra.models import Binary, Project
from chacra import util

logger = logging.getLogger(__name__)

class BinaryController:
    def __init__(self, binary_name: str, request: Request, db: Session):
        self.binary_name = binary_name
        self.project = db.query(Project).get(request.state.project_id)
        self.distro_version = request.state.distro_version
        self.distro = request.state.distro
        self.arch = request.state.arch
        self.ref = request.state.ref
        self.sha1 = request.state.sha1
        self.flavor = request.state.get('flavor', 'default')
        self.binary = db.query(Binary).filter_by(
            name=binary_name,
            ref=self.ref,
            sha1=self.sha1,
            distro=self.distro,
            distro_version=self.distro_version,
            flavor=self.flavor,
            arch=self.arch,
            project=self.project).first()

    async def index(self, response: Response):
        if not self.binary:
            raise HTTPException(status_code=404)
        response.headers['Content-Disposition'] = f'attachment; filename={self.binary.name}'
        if not os.getenv('DELEGATE_DOWNLOADS', False):
            return StreamingResponse(open(self.binary.path, 'rb'), media_type='application/octet-stream')
        else:
            relative_path = self.binary.path.split(os.getenv('BINARY_ROOT', '/tmp'))[-1].strip('/')
            path = os.path.join('/b/', relative_path)
            logger.info('setting path header: %s', path)
            response.headers['X-Accel-Redirect'] = path
            return Response(status_code=200)

    async def index_post(self, request: Request, db: Session):
        try:
            data = await request.json()
            name = data.get('name')
        except ValueError:
            raise HTTPException(status_code=400, detail='could not decode JSON body')

        if self.binary:
            if not data.get('force'):
                raise HTTPException(status_code=400, detail='file already exists and "force" flag was not used')
            else:
                path = data.get('path')
                if path:
                    try:
                        data['size'] = os.path.getsize(path)
                    except OSError:
                        logger.exception('could not retrieve size from %s' % path)
                        data['size'] = 0
                self.binary.update_from_json(data)
                db.commit()
                return {}

        if not name:
            raise HTTPException(status_code=400, detail="could not find required key: 'name'")
        name = data.pop('name')
        path = data.get('path')

        if path:
            size = os.path.getsize(path)
        else:
            size = 0
        binary = Binary(
            name=name, project=self.project, arch=self.arch,
            distro=self.distro, distro_version=self.distro_version,
            ref=self.ref, size=size, sha1=self.sha1
        )
        db.add(binary)
        db.commit()
        return {}

    async def index_put(self, file: UploadFile = File(...), db: Session = Depends(get_db)):
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail='no file object found in "file" param in POST request')
        self.binary.path = self.save_file(contents)
        db.commit()
        return {}

    async def index_delete(self, db: Session = Depends(get_db)):
        if not self.binary:
            raise HTTPException(status_code=404)
        binary_path = self.binary.path
        repo = self.binary.repo
        project = self.binary.project
        db.delete(self.binary)
        db.commit()
        try:
            if binary_path:
                os.remove(binary_path)
        except (IOError, OSError):
            msg = "Could not remove the binary path: %s" % binary_path
            logger.exception(msg)
            raise HTTPException(status_code=500, detail=msg)
        if repo.binaries.count() > 0:
            repo.needs_update = True
        else:
            db.delete(repo)
            db.commit()

        if project.binaries.count() == 0:
            db.delete(project)
            db.commit()

        return Response(status_code=204)

    def create_directory(self):
        end_part = request.url.path.split('binaries/')[-1].rstrip('/')
        end_part = end_part.split(self.binary_name)[0]
        path = os.path.join(os.getenv('BINARY_ROOT', '/tmp'), end_part.lstrip('/'))
        if not os.path.isdir(path):
            os.makedirs(path)
        return path

    def save_file(self, contents: bytes):
        dir_path = self.create_directory()
        if self.binary_name in os.listdir(dir_path):
            response_status = 200
        else:
            response_status = 201

        destination = os.path.join(dir_path, self.binary_name)

        with open(destination, 'wb') as f:
            f.write(contents)

        return destination

router = APIRouter()

@router.get('/{binary_name}', response_class=StreamingResponse)
async def get_binary(binary_name: str, request: Request, db: Session = Depends(get_db)):
    controller = BinaryController(binary_name, request, db)
    return await controller.index(request)

@router.post('/{binary_name}')
async def post_binary(binary_name: str, request: Request, db: Session = Depends(get_db)):
    controller = BinaryController(binary_name, request, db)
    return await controller.index_post(request, db)

@router.put('/{binary_name}')
async def put_binary(binary_name: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    controller = BinaryController(binary_name, request, db)
    return await controller.index_put(file, db)

@router.delete('/{binary_name}')
async def delete_binary(binary_name: str, db: Session = Depends(get_db)):
    controller = BinaryController(binary_name, request, db)
    return await controller.index_delete(db)