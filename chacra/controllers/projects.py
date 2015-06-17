from pecan import expose, abort, request
from chacra.models import projects
from chacra import models
from chacra.controllers import error, set_id_in_context
from chacra.controllers.refs import RefController


class ProjectController(object):

    def __init__(self, project_name):
        self.project_name = project_name
        self.project = projects.Project.query.filter_by(name=project_name).first()
        if not self.project:
            if request.method != 'POST':
                abort(404)
            elif request.method == 'POST':
                self.project = models.get_or_create(projects.Project, name=project_name)
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
