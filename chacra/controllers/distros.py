from pecan import expose, abort, request
from chacra import models
from chacra.controllers import error
from chacra.controllers.archs import ArchController


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
        return ArchController(name), remainder


class DistroController(object):
    def __init__(self, distro_name):
        self.distro_name = distro_name
        self.project = models.Project.get(request.context['project_id'])
        self.ref = request.context['ref']
        request.context['distro'] = distro_name

    @expose('json', generic=True)
    def index(self):
        # TODO: Improve this duplication here (and spread to other controllers)
        if self.distro_name not in self.project.distros:
            abort(404)
        if self.ref not in self.project.refs:
            abort(404)
        resp = {}

        for version in self.project.distro_versions:
            archs = [b.arch for b in models.Binary.filter_by(project=self.project, distro_version=version, distro=self.distro_name, ref=self.ref).all()]
            if archs:
                resp[version] = list(set(archs))
        return resp

    @index.when(method='POST', template='json')
    def index_post(self):
        error('/errors/not_allowed', 'POST requests to this url are not allowed')

    @expose()
    def _lookup(self, name, *remainder):
        return DistroVersionController(name), remainder
