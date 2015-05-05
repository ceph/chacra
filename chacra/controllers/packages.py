from pecan import expose, abort, request
from chacra.models import projects


class DistroController(object):

    def __init__(self, name):
        self.name = name
        project_id = request.context['project_id']
        self.project = projects.Project.get(project_id)

    @expose('json')
    def index(self):
        distro = self.project.get_distro(self.name)
        if not distro:
            abort(404)
        return distro


class DistrosController(object):

    def __init__(self, name):
        self.name = name
        project_id = request.context['project_id']
        self.project = projects.Project.get(project_id)

    @expose('json')
    def index(self):
        _id = request.context['project_id']
        project = projects.Project.get(_id)
        return project.distros

    @expose('json')
    def _lookup(self, name, *remainder):
        return DistroController(name), remainder


class PackageController(object):

    def __init__(self, project_name):
        self.project_name = project_name
        self.project = projects.Project.query.filter_by(name=project_name).first()
        if not self.project:
            abort(404)
        request.context['project_id'] = self.project.id

    @expose('json')
    def index(self):
        return self.package.distros

    @expose
    def _lookup(self, name, *remainder):
        return DistrosController(name), remainder


class PackagesController(object):

    @expose('json')
    def index(self):
        return projects.Project.query.all()

    @expose()
    def _lookup(self, project_name, *remainder):
        return PackageController(project_name), remainder
