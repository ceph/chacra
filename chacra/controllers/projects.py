from pecan import expose, abort, request
from chacra.models import Project
from chacra import models
from chacra.controllers import error
from chacra.controllers.refs import RefController


class ProjectController(object):

    def __init__(self, project_name):
        self.project_name = project_name
        self.project = Project.query.filter_by(name=project_name).first()
        if not self.project:
            if request.method != 'POST':
                abort(404)
            elif request.method == 'POST':
                self.project = models.get_or_create(Project, name=project_name)
        request.context['project_id'] = self.project.id

    @expose('json')
    def index(self):
        if request.method == 'POST':
            error('/errors/not_allowed', 'POST requests to this url are not allowed')
        return self.project

    @expose()
    def _lookup(self, name, *remainder):
        return RefController(name), remainder


class ProjectsController(object):

    @expose('json')
    def index(self):
        resp = {}
        for project in Project.query.all():
            resp[project.name] = project.refs
        return resp

    @expose()
    def _lookup(self, project_name, *remainder):
        return ProjectController(project_name), remainder
