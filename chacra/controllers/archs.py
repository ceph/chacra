import logging
import os
from pecan import expose, abort, request
from chacra.models import Binary
from chacra import models
from chacra.controllers import error
from chacra.controllers.binaries import BinaryController


logger = logging.getLogger(__name__)


class ArchController(object):

    def __init__(self, arch):
        self.arch = arch
        self.project = models.Project.get(request.context['project_id'])
        request.context['arch'] = self.arch
        self.distro = request.context['distro']
        self.distro_version = request.context['distro_version']
        self.arch = request.context['arch']
        self.ref = request.context['ref']

    @expose(generic=True, template='json')
    def index(self):
        if self.arch not in self.project.archs:
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

    @index.when(method='POST', template='json')
    def index_post(self):
        try:
            data = request.json
            name = data.get('name')
        except ValueError:
            error('/errors/invalid/', 'could not decode JSON body')

        # updates the binary only if explicitly told to do so
        binary = self.get_binary(name)
        if binary:
            if not data.get('force'):
                error('/errors/invalid/', 'file already exists and "force" flag was not used')
            else:
                # FIXME this looks like we need to implement PUT
                path = data.get('path')
                if path:
                    try:
                        data['size'] = os.path.getsize(path)
                    except OSError:
                        logger.exception('could not retrieve size from %s' % path)
                        data['size'] = 0
                binary.update_from_json(data)
                return {}

        # we allow empty data to be pushed
        if not name:
            error('/errors/invalid/', "could not find required key: 'name'")
        name = data.pop('name')
        path = data.get('path')

        if path:
            size = os.path.getsize(path)
        else:
            size = 0
        Binary(
            name=name, project=self.project, arch=self.arch,
            distro=self.distro, distro_version=self.distro_version,
            ref=self.ref, size=size
        )

        return {}

    @expose()
    def _lookup(self, name, *remainder):
        return BinaryController(name), remainder
