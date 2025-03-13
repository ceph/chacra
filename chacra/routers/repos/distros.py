from pecan import expose, abort, request
from chacra.models import Project
from chacra.controllers import error
from chacra.controllers.repos import RepoController


class DistroController(object):
    def __init__(self, distro_name):
        self.distro_name = distro_name
        self.project = Project.get(request.context['project_id'])
        self.ref = request.context['ref']
        self.sha1 = request.context['sha1']
        request.context['distro'] = distro_name

    @expose('json', generic=True)
    def index(self):
        # TODO: Improve this duplication here (and spread to other controllers)
        if self.distro_name not in self.project.repo_distros:
            abort(404)
        if self.ref not in self.project.repo_refs:
            abort(404)
        resp = []

        for repo in self.project.repos.filter_by(distro=self.distro_name, ref=self.ref, sha1=self.sha1).all():
            resp.append(repo.distro_version)
        return list(set(resp))

    @index.when(method='POST', template='json')
    def index_post(self):
        error('/errors/not_allowed',
              'POST requests to this url are not allowed')

    @expose()
    def _lookup(self, name, *remainder):
        return RepoController(name), remainder
