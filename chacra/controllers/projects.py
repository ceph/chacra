import os

import pecan
from pecan import expose, abort, request, response
from chacra.models import projects, Distro, DistroVersion, DistroArch, Binary, Ref
from chacra import models
from chacra.controllers import error


# TODO: move this out of here
def set_id_in_context(name, object_model, value):
    # if the object_model is None, then it will save it as None
    # saving us from having to do this everywhere
    object_name = name.split('_id')[0]
    if object_model is not None:
        request.context[name] = object_model.id
        request.context[object_name] = object_model.name
    else:
        request.context[name] = None
        request.context[object_name] = value


class BinaryController(object):

    def __init__(self, binary_name):
        self.binary_name = binary_name
        self.binary = Binary.query.filter_by(name=binary_name).first()
        self.arch = DistroArch.get(request.context['distro_arch_id'])
        if not self.binary and request.method != 'POST':
                abort(404)

    @expose('json', generic=True)
    def index(self):
        # TODO: implement downloads
        return dict(name=self.binary.name)

    @index.when(method='POST')
    def index_post(self):
        uploaded = request.POST.get('file', False)
        if uploaded is False:
            error('/errors/invalid/', 'no file object found in "file" param in POST request')
        file_obj = uploaded.file
        full_path = self.save_file(file_obj)
        if self.binary is None:
            Binary(self.binary_name, self.arch, path=full_path)
        else:
            self.binary.path = full_path
        return dict()

    def create_directory(self):
        end_part = request.url.split('projects/')[-1]
        # take out the binary name
        end_part = end_part.split(self.binary_name)[-1]
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


class ArchController(object):

    def __init__(self, arch_name):
        # archs are *not* unique, so we need to go by the distro version *and*
        # distro to ensure a level of uniqueness.
        self.arch_name = arch_name
        # if we have a distro already we can filter by that, otherwise we can just
        # create it later
        version = request.context.get('distro_version')
        self.distro_arch = DistroArch.filter_by(name=arch_name).join(
            DistroArch.version).filter(
                DistroVersion.name == version).first()

        if not self.distro_arch:
            if request.method != 'POST':
                abort(404)
            elif request.method == 'POST':
                version = DistroVersion.get(request.context['distro_version_id'])
                self.distro_arch = get_or_create(DistroArch, name=arch_name, version=version)

        set_id_in_context('distro_arch_id', self.distro_arch, arch_name)

    @expose(generic=True, template='json')
    def index(self):
        return dict(
            (d.name, d) for d in self.distro_arch.binaries.all()
        )

    @index.when(method='POST', template='json')
    def index_post(self):
        try:
            data = request.json
            name = data.get('name')
        except ValueError:
            error('/errors/invalid/', 'could not decode JSON body')

        # updates the binary only if explicitly told to do so
        binary = self.distro_arch.get_binary(name)
        if binary:
            if not data.get('force'):
                error('/errors/invalid/', 'file already exists and "force" flag was not used')
            else:
                binary.update_from_json(data)
                return {}

        # we allow empty data to be pushed
        if not name:
            error('/errors/invalid/', "could not find required key: 'name'")
        name = data.pop('name')
        self.ensure_objects(name, **data)
        return {}

    def ensure_objects(self, binary_name, **kw):
        """
        Since we might not have everything created, ensure everything is
        and push it to the database
        """
        project_id = request.context.get('project_id')
        distro_id = request.context.get('distro_id')
        version_id = request.context.get('distro_version_id')
        arch_id = request.context.get('distro_arch_id')
        ref_id = request.context.get('ref_id')
        is_none = lambda x: x is None
        if all(
                [is_none(i) for i in [project_id, distro_id, version_id, arch_id, ref_id]]):
            project = projects.Project(request.context['project'])
            ref = Ref(request.context['ref'], project)
            distro = Distro(request.context['distro'], ref)
            version = DistroVersion(request.context['distro_version'], distro)
            arch = DistroArch(request.context['distro_arch'], version)
            models.flush()
            models.commit()
            binary = Binary(binary_name, arch, **kw)
        else:  # we have some id's
            arch = self.distro_arch or DistroArch.get(request.context['distro_arch_id'])
            binary = Binary(binary_name, arch, **kw)
        return binary

    @expose()
    def _lookup(self, name, *remainder):
        return BinaryController(name), remainder


class DistroVersionController(object):

    def __init__(self, version_name):
        self.version_name = version_name
        self.distro_version = DistroVersion.query.filter_by(name=version_name).first()
        if not self.distro_version:
            if request.method != 'POST':
                abort(404)
            elif request.method == 'POST':
                distro = Distro.get(request.context['distro_id'])
                self.distro_version = get_or_create(
                    DistroVersion, name=version_name, distro=distro)
        set_id_in_context('distro_version_id', self.distro_version, version_name)

    @expose('json')
    def index(self):
        if request.method == 'POST':
            error('/errors/not_allowed', 'POST requests to this url are not allowed')
        return dict(
            (d.name, d) for d in self.distro_version.archs.all()
        )

    @expose()
    def _lookup(self, name, *remainder):
        return ArchController(name), remainder


class DistroController(object):
    def __init__(self, distro_name):
        self.distro_name = distro_name
        self.distro = Distro.query.filter_by(name=distro_name).first()
        if not self.distro:
            if request.method != 'POST':
                abort(404)
            elif request.method == 'POST':
                ref = Ref.get(request.context['ref_id'])
                self.distro = get_or_create(Distro, name=distro_name, ref=ref)
        set_id_in_context('distro_id', self.distro, distro_name)

    @expose('json')
    def index(self):
        if request.method == 'POST':
            error('/errors/not_allowed', 'POST requests to this url are not allowed')
        return dict(
            (d.name, d) for d in self.distro.versions.all()
        )

    @expose()
    def _lookup(self, name, *remainder):
        return DistroVersionController(name), remainder


class RefController(object):

    def __init__(self, ref_name):
        self.ref_name = ref_name
        self.ref = Ref.query.filter_by(name=ref_name).first()
        if not self.ref:
            if request.method != 'POST':
                abort(404)
            elif request.method == 'POST':
                project = projects.Project.get(request.context['project_id'])
                self.ref = get_or_create(Ref, name=ref_name, project=project)
        set_id_in_context('ref_id', self.ref, ref_name)

    @expose('json')
    def index(self):
        if request.method == 'POST':
            error('/errors/not_allowed', 'POST requests to this url are not allowed')

        return dict(
            (d.name, d) for d in self.ref.distros.all()
        )

    @expose()
    def _lookup(self, name, *remainder):
        return DistroController(name), remainder


def get_or_create(model, **kwargs):
    instance = model.filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        models.commit()
        return instance


class ProjectController(object):

    def __init__(self, project_name):
        self.project_name = project_name
        self.project = projects.Project.query.filter_by(name=project_name).first()
        if not self.project:
            if request.method != 'POST':
                abort(404)
            elif request.method == 'POST':
                self.project = get_or_create(projects.Project, name=project_name)
        set_id_in_context('project_id', self.project, project_name)

    @expose('json')
    def index(self):
        if request.method == 'POST':
            error('/errors/not_allowed', 'POST requests to this url are not allowed')
        return dict(
            (d.name, d) for d in self.project.refs.all()
        )

    @expose()
    def _lookup(self, name, *remainder):
        return RefController(name), remainder


class ProjectsController(object):

    @expose('json')
    def index(self):
        return dict(
            (p.name, p) for p in
            projects.Project.query.all()
        )

    @expose()
    def _lookup(self, project_name, *remainder):
        return ProjectController(project_name), remainder
