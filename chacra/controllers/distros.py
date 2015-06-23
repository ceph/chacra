from sqlalchemy.orm import subqueryload_all
from pecan import expose, abort, request
from chacra import models
from chacra.controllers import error, set_id_in_context
from chacra.controllers.archs import ArchController


class DistroVersionController(object):

    def __init__(self, version_name):
        self.version_name = version_name
        self.project = models.Project.get(request.context['project_id'])
        if self.ref_name not in self.project.refs:
            abort(404)

        self.distro_version = models.DistroVersion.filter_by(name=version_name, project=self.project).first()
        if not self.distro_version:
            if request.method != 'POST':
                abort(404)
            elif request.method == 'POST':
                distro = models.Distro.get(request.context['distro_id'])
                self.distro_version = models.get_or_create(
                    models.DistroVersion, name=version_name, distro=distro, project=self.project)
        set_id_in_context('distro_version_id', self.distro_version, version_name)

    @expose('json')
    def index(self):
        if request.method == 'POST':
            error('/errors/not_allowed', 'POST requests to this url are not allowed')
        return dict(
            (d.name, d) for d in self.distro_version.archs.all()
        )

    @expose()
    def _lookup(self, name, *remainder):
        return ArchController(name), remainder


class DistroController(object):
    def __init__(self, distro_name):
        self.distro_name = distro_name
        self.project = models.Project.get(request.context['project_id'])

    @expose('json', generic=True)
    def index(self):
        if self.distro_name not in self.project.distros:
            abort(404)
        resp = {}
        for version in self.project.distro_versions:
            archs = [b.arch for b in models.Binary.filter_by(project=self.project, distro_version=version, distro=self.distro_name).all()]
            if archs:
                resp[version] = archs
        return resp

    @index.when(method='POST')
    def index_post(self):
        error('/errors/not_allowed', 'POST requests to this url are not allowed')

    @expose()
    def _lookup(self, name, *remainder):
        return DistroVersionController(name), remainder
