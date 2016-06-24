import logging
import shutil

from pecan import expose, abort, request
from pecan.secure import secure
from pecan.ext.notario import validate

from chacra.models import Project
from chacra.controllers import error
from chacra.auth import basic_auth
from chacra import schemas


logger = logging.getLogger(__name__)


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

    @secure(basic_auth)
    @index.when(method='POST', template='json')
    @validate(schemas.repo_schema, handler='/errors/schema')
    def index_post(self):
        data = request.json
        self.repo.update_from_json(data)
        return self.repo

    @secure(basic_auth)
    @expose('json')
    def update(self):
        if request.method == 'HEAD':
            return {}
        if request.method != 'POST':
            error(
                '/errors/not_allowed',
                'only POST request are accepted for this url'
            )
        # Just mark the repo so that celery picks it up
        self.repo.needs_update = True
        self.repo.is_updating = False
        self.repo.is_queued = False
        return self.repo

    @secure(basic_auth)
    @expose('json')
    def recreate(self):
        if request.method == 'HEAD':
            return {}
        if request.method != 'POST':
            error(
                '/errors/not_allowed',
                'only POST request are accepted for this url'
            )
        # completely remove the path to the repository
        logger.info('removing repository path: %s', self.repo.path)
        try:
            shutil.rmtree(self.repo.path)
        except OSError:
            logger.warning("could not remove repo path: %s", self.repo.path)

        # mark the repo so that celery picks it up
        self.repo.needs_update = True
        self.repo.is_updating = False
        self.repo.is_queued = False
        return self.repo
