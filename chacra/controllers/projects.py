from pecan import expose, abort, request
from chacra.models import projects, Distro, DistroVersion, DistroArch, Binary


class BinaryController(object):

    def __init__(self, binary_name):
        self.binary_name = binary_name
        self.binary = Binary.query.filter_by(name=binary_name).first()
        if not self.binary:
            abort(404)

    @expose('json')
    def index(self):
        # TODO: implement downloads
        return dict(name=self.binary.name)


class ArchController(object):

    def __init__(self, arch_name):
        self.arch_name = arch_name
        self.distro_arch = DistroArch.query.filter_by(name=arch_name).first()
        if not self.distro_arch:
            abort(404)
        request.context['distro_arch_id'] = self.distro_arch.id

    @expose('json')
    def index(self):
        return dict(
            (d.name, d) for d in self.distro_arch.binaries.all()
        )


    @expose()
    def _lookup(self, name, *remainder):
        return BinaryController(name), remainder


class DistroVersionController(object):

    def __init__(self, version_name):
        self.version_name = version_name
        self.distro_version = DistroVersion.query.filter_by(name=version_name).first()
        if not self.distro_version:
            abort(404)
        request.context['distro_version_id'] = self.distro_version.id

    @expose('json')
    def index(self):
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
            abort(404)
        request.context['distro_id'] = self.distro.id

    @expose('json')
    def index(self):
        return dict(
            (d.name, d) for d in self.distro.versions.all()
        )

    @expose()
    def _lookup(self, name, *remainder):
        return DistroVersionController(name), remainder


class ProjectController(object):

    def __init__(self, project_name):
        self.project_name = project_name
        self.project = projects.Project.query.filter_by(name=project_name).first()
        if not self.project:
            abort(404)
        request.context['project_id'] = self.project.id

    @expose('json')
    def index(self):
        return dict(
            (d.name, d) for d in self.project.distros.all()
        )

    @expose()
    def _lookup(self, name, *remainder):
        return DistroController(name), remainder


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
