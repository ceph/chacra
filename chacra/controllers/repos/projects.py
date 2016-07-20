from pecan import expose, abort, request
from chacra.models import Project
from chacra.models.repos import Repo
from chacra.controllers import error
from chacra.controllers.repos.refs import RefController


class ProjectController(object):

    def __init__(self, project_name):
        self.project_name = project_name
        self.project = Project.query.filter_by(
            name=project_name
        ).join(Repo).filter(
            Repo.path != None
        ).first()
        if not self.project:
            abort(404)
        request.context['project_id'] = self.project.id

    @expose('json')
    def index(self):
        if request.method == 'POST':
            error('/errors/not_allowed',
                  'POST requests to this url are not allowed')
        resp = {}
        for ref in self.project.repo_refs:
            resp[ref] = list(set(
                [r.sha1 for r in
                    self.project.built_repos.filter_by(ref=ref).all()]
            ))
        return resp

    @expose()
    def _lookup(self, name, *remainder):
        return RefController(name), remainder


class ProjectsController(object):

    @expose('json')
    def index(self):
        resp = {}
        projects = Project.query.join(Repo).filter(Repo.path != None)
        for project in projects.all():
            resp[project.name] = project.repo_refs
        return resp

    @expose()
    def _lookup(self, project_name, *remainder):
        return ProjectController(project_name), remainder
