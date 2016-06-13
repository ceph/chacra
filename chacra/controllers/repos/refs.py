from pecan import expose, abort, request
from chacra.models import Project
from chacra.controllers import error
from chacra.controllers.repos.sha1s import SHA1Controller


class RefController(object):

    def __init__(self, ref_name):
        self.ref_name = ref_name
        self.project = Project.get(request.context['project_id'])
        request.context['ref'] = self.ref_name

    @expose('json', generic=True)
    def index(self):
        if self.ref_name not in self.project.repo_refs:
            abort(404)
        resp = {}
        sha1s = list(set(
            [r.sha1 for r in
                self.project.built_repos.filter_by(ref=self.ref_name).all()]
        ))
        for sha1 in sha1s:
            resp[sha1] = list(set(
                [b.distro for b in
                    self.project.built_repos.filter_by(ref=self.ref_name, sha1=sha1).all()]
            ))
        return resp

    @index.when(method='POST', template='json')
    def index_post(self):
        error('/errors/not_allowed',
              'POST requests to this url are not allowed')

    @expose()
    def _lookup(self, name, *remainder):
        return SHA1Controller(name), remainder
