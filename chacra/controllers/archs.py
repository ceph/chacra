from pecan import expose, abort, request
from chacra.models import Binary, Project
from chacra import models
from chacra.controllers import error, set_id_in_context
from chacra.models import get_or_create
from chacra.controllers.binaries import BinaryController


class ArchController(object):

    def __init__(self, arch):
        self.arch = arch
        self.project = models.Project.get(request.context['project_id'])
        request.context['arch'] = self.arch
        self.distro = request.context['distro']
        self.distro_version = request.context['distro_version']
        self.arch = request.context['arch']
        self.ref = request.context['ref']

    @expose(generic=True, template='json')
    def index(self):
        if self.arch not in self.project.archs:
            abort(404)

        resp = {}
        for b in self.project.binaries.filter_by(
                distro=self.distro,
                distro_version=self.distro_version,
                ref=self.ref,
                arch=self.arch).all():
            resp[b.name] = b
        return resp

    def get_binary(self, name):
        return Binary.filter_by(
            name=name, project=self.project, arch=self.arch,
            distro=self.distro, distro_version=self.distro_version,
            ref=self.ref
        ).first()

    @index.when(method='POST', template='json')
    def index_post(self):
        try:
            data = request.json
            name = data.get('name')
        except ValueError:
            error('/errors/invalid/', 'could not decode JSON body')

        # updates the binary only if explicitly told to do so
        binary = self.get_binary(name)
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
        Binary(
            name=name, project=self.project, arch=self.arch,
            distro=self.distro, distro_version=self.distro_version,
            ref=self.ref
        )


        #self.ensure_objects(name, **data)
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
            project = Project(request.context['project'])
            ref = Ref(request.context['ref'], project)
            distro = Distro(request.context['distro'], ref, project)
            version = DistroVersion(request.context['distro_version'], distro, project)
            arch = DistroArch(request.context['distro_arch'], version, project)
            models.flush()
            models.commit()
            binary = Binary(binary_name, arch, **kw)
        else:  # we have some id's
            project = Project.get(request.context['project_id'])
            arch = self.distro_arch or DistroArch.get(request.context['distro_arch_id'])
            binary = Binary(binary_name, arch, project, **kw)
        return binary

    @expose()
    def _lookup(self, name, *remainder):
        return BinaryController(name), remainder
