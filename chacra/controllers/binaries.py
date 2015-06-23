import os
import pecan
from pecan import expose, abort, request, response, conf
from webob.static import FileIter
from chacra.models import Binary, Project
from chacra.controllers import error


class BinaryController(object):

    def __init__(self, binary_name):
        self.binary_name = binary_name
        self.project = Project.get(request.context['project_id'])
        self.binary = Binary.query.filter_by(name=binary_name, project=self.project).first()

    @expose(content_type='application/octet-stream', generic=True)
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
        if not self.binary:
            abort(404)
        # we need to slap some headers so Nginx can serve this
        # TODO: maybe disable this for testing?
        # XXX Maybe we don't need to set Content-Disposition here?
        response.headers['Content-Disposition'] = 'attachment; filename=%s' % str(self.binary.name)
        response.headers['X-Accel-Redirect'] = str(self.binary.path)
        if conf.delegate_downloads is False:
            f = open(self.binary.path, 'rb')
            response.app_iter = FileIter(f)

    @index.when(method='POST')
    def index_post(self):
        contents = request.POST.get('file', False)
        if self.binary is not None:
            if os.path.exists(self.binary.path):
                if request.POST.get('force', False) is False:
                    error('/errors/invalid', "resource already exists and 'force' flag was not set")
        if contents is False:
            error('/errors/invalid/', 'no file object found in "file" param in POST request')
        file_obj = contents.file
        full_path = self.save_file(file_obj)
        if self.binary is None:
            path = full_path
            distro = request.context['distro']
            distro_version = request.context['distro_version']
            arch = request.context['arch']
            ref = request.context['ref']

            Binary(
                self.binary_name, self.project, arch=arch,
                distro=distro, distro_version=distro_version,
                ref=ref, path=path
            )
        else:
            self.binary.path = full_path
        return dict()

    def create_directory(self):
        end_part = request.url.split('projects/')[-1].rstrip('/')
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
            try:
                f.write(file_obj.getvalue())
            except AttributeError:
                f.write(file_obj.read())
        # return the full path to the saved object:
        return destination
