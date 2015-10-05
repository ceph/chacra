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
        if self.repo.path is None:
            abort(404)
        return self.repo

    @index.when(method='POST', template='json')
    def index_post(self):
        error('/errors/not_allowed',
              'POST requests to this url are not allowed')

    @expose('json', generic=True)
    def api(self):
        if self.distro_version not in self.project.repo_distro_versions:
            abort(404)

        if self.ref not in self.project.repo_refs:
            abort(404)

        if self.distro_name not in self.project.repo_distros:
            abort(404)

        return self.repo

    #TODO: post/delete will be supported eventually
    @api.when(method='POST', template='json')
    def api_post(self):
        error('/errors/not_allowed',
              'POST requests to this url are not allowed')

    @api.when(method='DELETE', template='json')
    def api_delete(self):
        error('/errors/not_allowed',
              'DELETE requests to this url are not allowed')
