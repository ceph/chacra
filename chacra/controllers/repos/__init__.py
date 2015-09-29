import datetime

from pecan import expose, abort, request
from chacra.models import Project
from chacra import models
from chacra.controllers import error


class RepoController(object):

    def __init__(self, distro_version):
        self.distro_version = distro_version
        self.project = Project.get(request.context['project_id'])
        self.distro_name = request.context['distro']
        self.ref = request.context['ref']
        request.context['distro_version'] = self.distro_version

    @expose('json', generic=True)
    def index(self):
        if self.distro_version not in self.project.distro_versions:
            abort(404)

        # TODO: actually query the repo model which doesn't exist yet
        resp = dict(
            needs_update=False,
            last_built=datetime.datetime.now(),
            modified=datetime.datetime.now(),
            signed=False,
            size=1024,
        )
        return resp

    @index.when(method='POST', template='json')
    def index_post(self):
        error('/errors/not_allowed',
              'POST requests to this url are not allowed')
