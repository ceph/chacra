import os
import logging
import pecan
from pecan import expose, abort, request, response, conf
from pecan.secure import secure
from webob.static import FileIter
from chacra.models import Binary, Project
from chacra.controllers import error
from chacra.auth import basic_auth

logger = logging.getLogger(__name__)


class BinaryController(object):

    def __init__(self, binary_name):
        self.binary_name = binary_name
        self.project = Project.get(request.context['project_id'])
        self.distro_version = request.context['distro_version']
        self.distro = request.context['distro']
        self.arch = request.context['arch']
        self.ref = request.context['ref']
        self.binary = Binary.query.filter_by(
            name=binary_name,
            ref=self.ref,
            distro=self.distro,
            distro_version=self.distro_version,
            project=self.project).first()

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
        if conf.delegate_downloads is False:
            f = open(self.binary.path, 'rb')
            response.app_iter = FileIter(f)
        else:
            relative_path = self.binary.path.split(pecan.conf.binary_root)[-1].strip('/')
            # FIXME: this should be read from configuration, this is not configurable
            # at the moment and relies on the nginx config being properly set
            path = os.path.join('/b/', relative_path)
            logger.info('setting path header: %s', path)
            response.headers['X-Accel-Redirect'] = path

    @secure(basic_auth)
    @index.when(method='POST', template='json')
    def index_post(self):
        try:
            data = request.json
            name = data.get('name')
        except ValueError:
            error('/errors/invalid/', 'could not decode JSON body')

        # updates the binary only if explicitly told to do so
        if self.binary:
            if not data.get('force'):
                error('/errors/invalid/', 'file already exists and "force" flag was not used')
            else:
                # FIXME this looks like we need to implement PUT
                path = data.get('path')
                if path:
                    try:
                        data['size'] = os.path.getsize(path)
                    except OSError:
                        logger.exception('could not retrieve size from %s' % path)
                        data['size'] = 0
                self.binary.update_from_json(data)
                return {}

        # we allow empty data to be pushed
        if not name:
            error('/errors/invalid/', "could not find required key: 'name'")
        name = data.pop('name')
        path = data.get('path')

        if path:
            size = os.path.getsize(path)
        else:
            size = 0
        Binary(
            name=name, project=self.project, arch=self.arch,
            distro=self.distro, distro_version=self.distro_version,
            ref=self.ref, size=size
        )

        return {}

    @secure(basic_auth)
    @index.when(method='PUT', template='json')
    def index_put(self):
        contents = request.POST.get('file', False)
        if contents is False:
            error('/errors/invalid/', 'no file object found in "file" param in POST request')
        file_obj = contents.file
        # this looks odd, path is not changing, but we need to 'ping' the object by
        # re-saving the attribute so that the listener can update the checksum and modified
        # timestamps
        self.binary.path = self.save_file(file_obj)
        return dict()

    @secure(basic_auth)
    @index.when(method='DELETE', template='json')
    def index_delete(self):
        if not self.binary:
            abort(404)
        binary_path = self.binary.path
        repo = self.binary.repo
        project = self.binary.project
        self.binary.delete()
        try:
            os.remove(binary_path)
        except (IOError, OSError):
            msg = "Could not remove the binary path: %s" % binary_path
            logger.exception(msg)
            error('/errors/error/', msg)
        if repo.binaries.count() > 0:
            # there are still binaries related to this repo, mark it to rebuild
            repo.needs_update = True
        else:
            # there are no more binaries for this repo, delete the repo
            repo.delete()

        if project.binaries.count() == 0:
            project.delete()

        response.status = 204
        return dict()

    def create_directory(self):
        end_part = request.url.split('binaries/')[-1].rstrip('/')
        # take out the binary name
        end_part = end_part.split(self.binary_name)[0]
        path = os.path.join(pecan.conf.binary_root, end_part.lstrip('/'))
        if not os.path.isdir(path):
            os.makedirs(path)
        return path

    def save_file(self, file_obj):
        # TODO: we should just use self.binary.path for this
        dir_path = self.create_directory()
        if self.binary_name in os.listdir(dir_path):
            # resource exists so we will update it
            response.status = 200
        else:
            # TODO: enforce this.
            # we will create a resource, but this SHOULD NOT HAPPEN
            # because we are PUT not POST
            response.status = 201

        destination = os.path.join(dir_path, self.binary_name)

        with open(destination, 'wb') as f:
            file_iterable = FileIter(file_obj)
            for chunk in file_iterable:
                f.write(chunk)

        # return the full path to the saved object:
        return destination
