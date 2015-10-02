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

    @expose(content_type='text/html', generic=True)
    def index(self):
        """
        Special method for internal redirect URI's so that webservers (like
        Nginx) can serve downloads to clients while the app just delegates.
        This method will require an Nginx configuration that points to
        resources and match `binary_root` URIs::

            location /home/ubuntu/repos/ {
              internal;
              alias   /files/;
            }

        `alias` can be anything, it would probably make sense to have a set of rules that allow
        distinct URIs, like::

            location /home/ubuntu/repos/rpm-firefly/ {
              internal;
              alias   /files/rpm-firefly/;
            }


        There are two ways to get binaries into this app: via existing files in
        certain paths POSTing JSON to the arch/ endpoint, or via actual upload
        of the binary. So if many locations need to be supported, they each
        need to have a corresponding section in Nginx to be configured.
        """
        if self.distro_version not in self.project.repo_distro_versions:
            abort(404)

        if self.repo.path is None:
            abort(404)

        #TODO: nginx should serve the path to the repo directory
        return "Nginx to serve: %s" % (self.repo.path)

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
