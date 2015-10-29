import logging
import os
import pecan
from pecan import response
from pecan.secure import secure
from pecan import expose, abort, request
from chacra.models import Binary
from chacra import models
from chacra.controllers import error
from chacra.controllers.binaries import BinaryController
from chacra.auth import basic_auth


logger = logging.getLogger(__name__)


class ArchController(object):

    def __init__(self, arch):
        self.arch = arch
        self.project = models.Project.get(request.context['project_id'])
        self.distro = request.context['distro']
        self.distro_version = request.context['distro_version']
        self.ref = request.context['ref']
        request.context['arch'] = self.arch

    @expose(generic=True, template='json')
    def index(self):
        if self.arch not in self.project.archs:
            abort(404)

        binaries = self.project.binaries.filter_by(
            distro=self.distro,
            distro_version=self.distro_version,
            ref=self.ref,
            arch=self.arch).all()

        if not binaries:
            abort(404)

        resp = {}
        for b in self.project.binaries.filter_by(
                distro=self.distro,
                distro_version=self.distro_version,
                ref=self.ref,
                arch=self.arch).all():
            resp[b.name] = b
        return resp

    def get_binary(self, name):
        return Binary.filter_by(
            name=name, project=self.project, arch=self.arch,
            distro=self.distro, distro_version=self.distro_version,
            ref=self.ref
        ).first()

    @secure(basic_auth)
    @index.when(method='POST', template='json')
    def index_post(self):
        contents = request.POST.get('file', False)
        if contents is False:
            error('/errors/invalid/', 'no file object found in "file" param in POST request')
        file_obj = contents.file
        filename = contents.filename
        self.binary = self.get_binary(filename)
        self.binary_name = filename
        if self.binary is not None:
            if os.path.exists(self.binary.path):
                if request.POST.get('force', False) is False:
                    error('/errors/invalid', "resource already exists")

        full_path = self.save_file(file_obj)

        if self.binary is None:
            path = full_path
            distro = request.context['distro']
            distro_version = request.context['distro_version']
            arch = request.context['arch']
            ref = request.context['ref']

            Binary(
                self.binary_name, self.project, arch=arch,
                distro=distro, distro_version=distro_version,
                ref=ref, path=path, size=os.path.getsize(path)
            )
        else:
            self.binary.path = full_path
        return dict()

    def create_directory(self):
        end_part = request.url.split('binaries/')[-1].rstrip('/')
        # take out the binary name
        end_part = end_part.split(self.binary_name)[0]
        path = os.path.join(pecan.conf.binary_root, end_part.lstrip('/'))
        if not os.path.isdir(path):
            os.makedirs(path)
        return path

    def save_file(self, file_obj):
        dir_path = self.create_directory()
        if self.binary_name in os.listdir(dir_path):
            # resource exists so we will update it
            response.status = 200
        else:
            # we will create a resource
            response.status = 201

        destination = os.path.join(dir_path, self.binary_name)
        with open(destination, 'wb') as f:
            try:
                f.write(file_obj.getvalue())
            except AttributeError:
                f.write(file_obj.read())
        # return the full path to the saved object:
        return destination

    @expose()
    def _lookup(self, name, *remainder):
        return BinaryController(name), remainder
