from pecan import expose, abort, request
from chacra import models
from chacra.controllers import error
from chacra.controllers.binaries.distros import DistroController


class SHA1Controller(object):

    def __init__(self, sha1):
        self.sha1 = sha1
        self.project = models.Project.get(request.context['project_id'])
        request.context['sha1'] = sha1
        self.ref = request.context["ref"]

    @expose('json', generic=True)
    def index(self):
        if self.sha1 not in self.project.sha1s:
            abort(404)
        resp = {}
        binaries = models.Binary.filter_by(
            project=self.project,
            sha1=self.sha1,
            ref=self.ref).all()

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
