from pecan import expose, abort, request
from chacra.models import projects, Distro, DistroVersion, DistroArch, Binary, Ref
from chacra import models
from chacra.controllers import error, set_id_in_context
from chacra.models import get_or_create
from chacra.controllers.binaries import BinaryController


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
