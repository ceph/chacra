import logging
import shutil

from pecan import expose, abort, request
from pecan.secure import secure
from pecan.ext.notario import validate

from chacra.models import Project
from chacra.controllers import error
from chacra.auth import basic_auth
from chacra import schemas, async


logger = logging.getLogger(__name__)


class FlavorsController(object):

    def __init__(self):
        self.distro_version = request.context['distro_version']
        self.project = Project.get(request.context['project_id'])
        self.distro_name = request.context['distro']
        self.ref = request.context['ref']
        self.sha1 = request.context['sha1']
        self.repos = self.project.repos.filter_by(
            distro=self.distro_name,
            distro_version=self.distro_version,
            ref=self.ref,
            sha1=self.sha1,
        ).all()
        self.flavors = list(set([r.flavor for r in self.repos]))

    @expose('json', generic=True)
    def index(self):
        return self.flavors

    @index.when(method='POST', template='json')
    def index_post(self):
        error('/errors/not_allowed', 'POST requests to this url are not allowed')

    @expose()
    def _lookup(self, flavor, *remainder):
        if flavor not in self.flavors:
            abort(404)
        return RepoController(self.distro_version, flavor), remainder


class RepoController(object):

    def __init__(self, distro_version, flavor=None):
        self.distro_version = distro_version
        self.project = Project.get(request.context['project_id'])
        self.distro_name = request.context['distro']
        self.ref = request.context['ref']
        self.sha1 = request.context['sha1']
        if not request.context.get('distro_version'):
            request.context['distro_version'] = self.distro_version
        self.flavor = flavor
        self.repo_obj = self.project.repos.filter_by(
            distro=self.distro_name,
            distro_version=self.distro_version,
            ref=self.ref,
            sha1=self.sha1,
            flavor=self.flavor or 'default',
        ).first()

    @expose('json', generic=True)
    def index(self):
        if self.repo_obj is None:
            print "no repo, aborting"
            abort(404)
        return self.repo_obj

    @secure(basic_auth)
    @index.when(method='POST', template='json')
    @validate(schemas.repo_schema, handler='/errors/schema')
    def index_post(self):
        data = request.json
        self.repo_obj.update_from_json(data)
        return self.repo_obj

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
        self.repo_obj.needs_update = True
        self.repo_obj.is_updating = False
        self.repo_obj.is_queued = False

        async.post_requested(self.repo_obj)
        return self.repo_obj

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
        logger.info('removing repository path: %s', self.repo_obj.path)
        try:
            shutil.rmtree(self.repo_obj.path)
        except OSError:
            logger.warning("could not remove repo path: %s", self.repo_obj.path)

        # mark the repo so that celery picks it up
        self.repo_obj.needs_update = True
        self.repo_obj.is_updating = False
        self.repo_obj.is_queued = False

        async.post_requested(self.repo_obj)
        return self.repo_obj

    @secure(basic_auth)
    @expose('json')
    def extra(self):
        if request.method != 'POST':
            error(
                '/errors/not_allowed',
                'only POST request are accepted for this url'
            )
        self.repo_obj.extra = request.json
        return self.repo_obj

    @expose('mako:repo.mako')
    def repo(self):
        return dict(
            project_name=self.project.name,
            base_url=self.repo_obj.base_url,
            distro_version=self.repo_obj.distro_version,
            type=self.repo_obj.type,
        )

    @expose()
    def _lookup(self, name, *remainder):
        # the `is not None` prevents this from being a recursive url
        if name == 'flavors' and self.flavor is None:
            return FlavorsController(), remainder
        abort(404)
