from pecan import expose, abort, request
from chacra.models import Project, Binary
from chacra.controllers import error
from chacra.controllers.repos.distros import DistroController


class SHA1Controller(object):

    def __init__(self, sha1):
        self.sha1 = sha1
        self.project = Project.get(request.context['project_id'])
        self.ref = request.context['ref']
        request.context['sha1'] = sha1

    @expose('json', generic=True)
    def index(self):
        if self.sha1 not in self.project.repo_sha1s:
            abort(404)
        resp = {}
        for distro in self.project.repo_distros:
            resp[distro] = list(set(
                [b.distro_version for b in
                    self.project.built_repos.filter_by(distro=distro, ref=self.ref, sha1=self.sha1).all()]
            ))
        return resp

    @index.when(method='POST', template='json')
    def index_post(self):
        error('/errors/not_allowed',
              'POST requests to this url are not allowed')

    @expose()
    def _lookup(self, name, *remainder):
        return DistroController(name), remainder
