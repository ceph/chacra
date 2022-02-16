import logging
import os
import shutil

from pecan import expose, abort, request, response
from pecan.secure import secure
from pecan.ext.notario import validate

from chacra.models import Project
from chacra.controllers import error
from chacra.auth import basic_auth
from chacra import schemas, asynch
from chacra import util


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
            print("no repo, aborting")
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
        if self.repo_obj.type == 'raw':
            # raw repos need no asynch construction.  Create
            # the paths, symlink the binaries, mark them ready.
            self.repo_obj.path = util.repo_paths(self.repo_obj)['absolute']
            util.makedirs(self.repo_obj.path)
            for binary in self.repo_obj.binaries:
                src = binary.path
                dest = os.path.join(
                        self.repo_obj.path,
                        os.path.join(binary.arch, binary.name)
                       )
                try:
                    if not os.path.exists(dest):
                        os.symlink(src, dest)
                except OSError:
                    logger.exception(
                        f'could not symlink raw binary {src} -> {dest}')

            self.repo_obj.needs_update = False
            asynch.post_ready(self.repo_obj)
        else:
            # Just mark the repo so that celery picks it up
            self.repo_obj.needs_update = True
            self.repo_obj.is_updating = False
            self.repo_obj.is_queued = False
            asynch.post_requested(self.repo_obj)

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

        asynch.post_requested(self.repo_obj)
        return self.repo_obj

    @secure(basic_auth)
    @index.when(method='DELETE', template='json')
    @validate(schemas.repo_schema, handler='/errors/schema')
    def index_delete(self):
        repo_path = self.repo_obj.path
        logger.info('nuke repository path: %s', repo_path)
        try:
            shutil.rmtree(repo_path)
        except OSError:
            msg = "could not remove repo path: {}".format(repo_path)
            logger.exception(msg)
            error('/errors/error/', msg)
        for binary in self.repo_obj.binaries:
            binary_path = binary.binary.path
            if binary_path:
                try:
                    os.remove(binary_path)
                except (IOError, OSError):
                    msg = "Could not remove the binary path: %s" % binary_path
                    logger.exception(msg)
            binary.delete()
        self.repo_obj.delete()
        if self.project.repos.count() == 0:
            self.project.delete()
        response.status = 204
        return dict()

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

    @expose('mako:repo.mako', content_type="text/plain")
    def repo(self):
        return dict(
            project_name=self.project.name,
            base_url=self.repo_obj.base_url,
            distro_name=self.distro_name.lower(),
            distro_version=self.repo_obj.distro_version,
            type=self.repo_obj.type,
        )

    @expose()
    def _lookup(self, name, *remainder):
        # the `is not None` prevents this from being a recursive url
        if name == 'flavors' and self.flavor is None:
            return FlavorsController(), remainder
        abort(404)
