import logging
import os
import shutil

from pecan import expose, abort, request, response, conf
from pecan.secure import secure
from pecan_notario import validate

from chacra.models import Project
from chacra.controllers import error
from chacra.auth import basic_auth
from chacra import schemas, asynch
from chacra import locks, util


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
        if self.repo_obj is None:
            abort(404)
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
        if self.repo_obj is None:
            abort(404)
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
            self.request_build()
            asynch.post_requested(self.repo_obj)

        return self.repo_obj

    def request_build(self, lock=None):
        """
        Mark the repo as needing an update, which is all it takes for a build
        that is queued or running: a queued build didn't start to collect
        binaries yet, and when a running one completes the repo will get
        queued again.

        ``is_updating`` and ``is_queued`` are reset only if they are stale,
        otherwise a second build for the same repo would get queued while the
        first one is still working on it. They are stale when no build is
        holding the lock for the repo (the worker died), or when the repo has
        been queued for too long (the task got lost).

        ``lock`` is the lock for the repo, if the caller is holding it.
        """
        repo = self.repo_obj
        stale_after = getattr(conf, 'queued_stale_after', 3600)
        # has to be checked before anything changes in the repo
        queued_for = util.seconds_since_modified(repo) if repo.is_queued else None

        repo.needs_update = True
        if repo.is_updating and (lock or not locks.is_locked(repo.id)):
            logger.warning('%s is not being built, resetting is_updating', repo)
            repo.is_updating = False
        if queued_for is not None and queued_for > stale_after:
            logger.warning(
                '%s was queued %s seconds ago, resetting is_queued',
                repo, int(queued_for)
            )
            repo.is_queued = False

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
        if self.repo_obj is None:
            abort(404)
        lock = locks.RepoLock(self.repo_obj.id)
        if lock.acquire():
            try:
                # completely remove the path to the repository, unless the
                # repo was never built and has no path yet
                if self.repo_obj.path:
                    logger.info('removing repository path: %s', self.repo_obj.path)
                    try:
                        shutil.rmtree(self.repo_obj.path)
                    except OSError:
                        logger.warning("could not remove repo path: %s", self.repo_obj.path)
                # mark the repo so that celery picks it up
                self.request_build(lock)
            finally:
                lock.release()
        else:
            # the path can't be removed while the repo is being built, the
            # next build will do it
            logger.info('%s is being built, will be recreated by the next build', self.repo_obj)
            locks.request_recreate(self.repo_obj.id)
            self.request_build()

        asynch.post_requested(self.repo_obj)
        return self.repo_obj

    @secure(basic_auth)
    @index.when(method='DELETE', template='json')
    @validate(schemas.repo_schema, handler='/errors/schema')
    def index_delete(self):
        if self.repo_obj is None:
            abort(404)
        repo_path = self.repo_obj.path
        if repo_path:
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
        locks.forget(self.repo_obj.id)
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
        if self.repo_obj is None:
            abort(404)
        self.repo_obj.extra = request.json
        return self.repo_obj

    @expose('mako:repo.mako', content_type="text/plain")
    def repo(self):
        if self.repo_obj is None:
            abort(404)
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
