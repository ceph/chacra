from pecan import expose, abort, request
from chacra.models import Project
from chacra.controllers import error


class RepoController(object):

    def __init__(self, distro_version):
        self.distro_version = distro_version
        self.project = Project.get(request.context['project_id'])
        self.distro_name = request.context['distro']
        self.ref = request.context['ref']
        request.context['distro_version'] = self.distro_version
        self.repo = self.project.built_repos.filter_by(
            distro=self.distro_name,
            distro_version=self.distro_version,
            ref=self.ref,
        ).first()

    @expose('json', generic=True)
    def index(self):
        if self.repo is None:
            abort(404)
        return self.repo

    @index.when(method='POST', template='json')
    def index_post(self):
        error('/errors/not_allowed',
              'POST requests to this url are not allowed')
