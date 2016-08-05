import os
import logging
import pecan
from pecan import expose, abort, request, response
from pecan.secure import secure
from webob.static import FileIter
from chacra import models, util
from chacra.controllers import error
from chacra.controllers.util import repository_is_automatic
from chacra.controllers.binaries import BinaryController
from chacra.auth import basic_auth

logger = logging.getLogger(__name__)


class FlavorController(object):

    def __init__(self, flavor):
        self.flavor = flavor
        self.arch = request.context['arch']
        self.project = models.Project.get(request.context['project_id'])
        self.distro = request.context['distro']
        self.distro_version = request.context['distro_version']
        self.ref = request.context['ref']
        self.sha1 = request.context['sha1']
        request.context['flavor'] = self.flavor

    @expose(generic=True, template='json')
    def index(self):
        abort(405)

    @index.when(method='HEAD', template='json')
    def index_head(self):
        binaries = self.project.binaries.filter_by(
            distro=self.distro,
            distro_version=self.distro_version,
            ref=self.ref,
            sha1=self.sha1,
            flavor=self.flavor,
            arch=self.arch).all()

        if not binaries:
            abort(404)
        return dict()

    @index.when(method='GET', template='json')
    def index_get(self):
        binaries = self.project.binaries.filter_by(
            distro=self.distro,
            distro_version=self.distro_version,
            ref=self.ref,
            sha1=self.sha1,
            flavor=self.flavor,
            arch=self.arch).all()

        if not binaries:
            abort(404)

        resp = {}
        for b in self.project.binaries.filter_by(
                distro=self.distro,
                distro_version=self.distro_version,
                ref=self.ref,
                sha1=self.sha1,
                flavor=self.flavor,
                arch=self.arch).all():
            resp[b.name] = b
        return resp

    def get_binary(self, name):
        return models.Binary.filter_by(
            name=name, project=self.project, arch=self.arch,
            distro=self.distro, distro_version=self.distro_version,
            ref=self.ref, sha1=self.sha1, flavor=self.flavor
        ).first()

    @secure(basic_auth)
    @index.when(method='POST', template='json')
    def index_post(self):
        contents = request.POST.get('file', False)
        if contents is False:
            error('/errors/invalid/', 'no file object found in "file" param in POST request')
        file_obj = contents.file
        filename = contents.filename
        self.binary = self.get_binary(filename)
        self.binary_name = filename
        if self.binary is not None:
            if os.path.exists(self.binary.path):
                if request.POST.get('force', False) is False:
                    error('/errors/invalid', 'resource already exists and "force" key was not used')

        full_path = self.save_file(file_obj)

        if self.binary is None:
            path = full_path
            distro = request.context['distro']
            distro_version = request.context['distro_version']
            arch = request.context['arch']
            ref = request.context['ref']
            sha1 = request.context['sha1']

            self.binary = models.Binary(
                self.binary_name, self.project, arch=arch,
                distro=distro, distro_version=distro_version,
                ref=ref, sha1=sha1, path=path, size=os.path.getsize(path),
                flavor=self.flavor
            )
        else:
            self.binary.path = full_path

        # check if this binary is interesting for other configured projects,
        # and if so, then mark those other repos so that they can be re-built
        self.mark_related_repos()

        return dict()

    def mark_related_repos(self):
        related_projects = util.get_related_projects(self.project.name)
        repos = []
        projects = []
        for project_name, refs in related_projects.items():
            p = models.projects.get_or_create(name=project_name)
            projects.append(p)
            repo_query = []
            if refs == ['all']:
                # we need all the repos available
                repo_query = models.Repo.filter_by(project=p).all()
            else:
                for ref in refs:
                    repo_query = models.Repo.filter_by(project=p, ref=ref).all()
            if repo_query:
                for r in repo_query:
                    repos.append(r)

        if not repos:
            # there are no repositories associated with this project, so go ahead
            # and create one so that it can be queried by the celery task later
            for project in projects:
                repo = models.Repo(
                    project,
                    self.ref,
                    self.distro,
                    self.distro_version,
                    sha1=self.sha1,
                )
                repo.needs_update = repository_is_automatic(project.name)
                repo.type = self.binary._get_repo_type()

        else:
            for repo in repos:
                repo.needs_update = repository_is_automatic(repo.project.name)
                if repo.type is None:
                    repo.type = self.binary._get_repo_type()

    def create_directory(self):
        end_part = request.url.split('binaries/')[-1].rstrip('/')
        # take out the binary name
        end_part = end_part.split(self.binary_name)[0]
        path = os.path.join(pecan.conf.binary_root, end_part.lstrip('/'))
        if not os.path.isdir(path):
            os.makedirs(path)
        return path

    def save_file(self, file_obj):
        dir_path = self.create_directory()
        if self.binary_name in os.listdir(dir_path):
            # resource exists so we will update it
            response.status = 200
        else:
            # we will create a resource
            response.status = 201

        destination = os.path.join(dir_path, self.binary_name)

        with open(destination, 'wb') as f:
            file_iterable = FileIter(file_obj)
            for chunk in file_iterable:
                f.write(chunk)

        # return the full path to the saved object:
        return destination

    @expose()
    def _lookup(self, name, *remainder):
        return BinaryController(name), remainder


class FlavorsController(object):

    @expose('json', generic=True)
    def index(self):
        project = models.Project.get(request.context['project_id'])
        resp = {}
        for flavor in project.flavors:
            binaries = [
                b.name for b in models.Binary.filter_by(
                    project=project,
                    distro_version=request.context['distro_version'],
                    distro=request.context['distro'],
                    ref=request.context['ref'],
                    sha1=request.context['sha1'],
                    arch=request.context['arch']).all()]
            if binaries:
                resp[flavor] = list(set(binaries))
        return resp

    @index.when(method='POST', template='json')
    def index_post(self):
        error('/errors/not_allowed', 'POST requests to this url are not allowed')

    @expose()
    def _lookup(self, flavor, *remainder):
        if request.method in ['HEAD', 'GET']:
            project = models.Project.get(request.context['project_id'])
            if flavor not in project.flavors:
                abort(404)
        return FlavorController(flavor), remainder
