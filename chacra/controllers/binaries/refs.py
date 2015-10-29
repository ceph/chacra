from pecan import expose, abort, request
from chacra import models
from chacra.controllers import error
from chacra.controllers.binaries.distros import DistroController


class RefController(object):

    def __init__(self, ref_name):
        self.ref_name = ref_name
        self.project = models.Project.get(request.context['project_id'])
        request.context['ref'] = self.ref_name

    @expose('json', generic=True)
    def index(self):
        if self.ref_name not in self.project.refs:
            abort(404)
        resp = {}
        binaries = models.Binary.filter_by(
            project=self.project,
            ref=self.ref_name).all()

        distros = set([b.distro for b in binaries])

        for distro in distros:
            resp[distro] = list(
                set(
                    [b.distro_version for b in binaries if b.distro == distro ]
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
        return DistroController(name), remainder
