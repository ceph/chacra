from pecan import expose, abort, request
from chacra import models
from chacra.controllers import error, set_id_in_context
from chacra.controllers.archs import ArchController


class DistroVersionController(object):

    def __init__(self, version_name):
        self.version_name = version_name
        self.distro_version = models.DistroVersion.query.filter_by(name=version_name).first()
        if not self.distro_version:
            if request.method != 'POST':
                abort(404)
            elif request.method == 'POST':
                distro = models.Distro.get(request.context['distro_id'])
                self.distro_version = models.get_or_create(
                    models.DistroVersion, name=version_name, distro=distro)
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
        self.distro = models.Distro.query.filter_by(name=distro_name).first()
        if not self.distro:
            if request.method != 'POST':
                abort(404)
            elif request.method == 'POST':
                ref = models.Ref.get(request.context['ref_id'])
                self.distro = models.get_or_create(models.Distro, name=distro_name, ref=ref)
        set_id_in_context('distro_id', self.distro, distro_name)

    @expose('json')
    def index(self):
        if request.method == 'POST':
            error('/errors/not_allowed', 'POST requests to this url are not allowed')
        return dict(
            (d.name, d) for d in self.distro.versions.all()
        )

    @expose()
    def _lookup(self, name, *remainder):
        return DistroVersionController(name), remainder
