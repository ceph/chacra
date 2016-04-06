from pecan import expose, abort, request
from chacra import models
from chacra.controllers import error
from chacra.controllers.binaries.archs import ArchController


class DistroVersionController(object):

    def __init__(self, distro_version):
        self.distro_version = distro_version
        self.project = models.Project.get(request.context['project_id'])
        self.distro_name = request.context['distro']
        self.ref = request.context['ref']
        request.context['distro_version'] = self.distro_version

    @expose('json', generic=True)
    def index(self):
        if self.distro_version not in self.project.distro_versions:
            abort(404)

        resp = {}
        for arch in self.project.archs:
            binaries = [
                b.name for b in models.Binary.filter_by(
                    project=self.project,
                    distro_version=self.distro_version,
                    distro=self.distro_name,
                    ref=self.ref,
                    arch=arch).all()]
            if binaries:
                resp[arch] = list(set(binaries))
        return resp

    @index.when(method='POST', template='json')
    def index_post(self):
        error('/errors/not_allowed', 'POST requests to this url are not allowed')

    @expose()
    def _lookup(self, name, *remainder):
        if request.method in  ['HEAD', 'GET']:
            if self.distro_version not in self.project.distro_versions:
                abort(404)
        return ArchController(name), remainder


class DistroController(object):
    def __init__(self, distro_name):
        self.distro_name = distro_name
        self.project = models.Project.get(request.context['project_id'])
        self.ref = request.context['ref']
        request.context['distro'] = distro_name

    @expose('json', generic=True)
    def index(self):
        resp = {}

        binaries = models.Binary.filter_by(
            project=self.project,
            distro=self.distro_name,
            ref=self.ref).all()

        if not binaries:
            abort(404)

        distro_versions = set([b.distro_version for b in binaries])

        for distro_version in distro_versions:
            resp[distro_version] = list(
                set(
                    [b.arch for b in binaries if b.distro_version == distro_version]
                )
            )
        if not resp:
            abort(404)
        return resp

    @index.when(method='POST', template='json')
    def index_post(self):
        error('/errors/not_allowed', 'POST requests to this url are not allowed')

    @expose()
    def _lookup(self, name, *remainder):
        return DistroVersionController(name), remainder
