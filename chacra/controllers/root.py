from pecan import expose
from chacra.models import Project, Repo
from chacra.controllers.projects import ProjectsController
from chacra.controllers.errors import ErrorsController
from chacra.controllers.search import SearchController
from chacra.controllers.repos.projects import (
    ProjectsController as RepoProjectsController,
)


description = """chacra is a binary API that allows querying, posting,
updating, and retrieving binaries for different projects."""


class RootController(object):

    @expose('json')
    def index(self):
        documentation = "https://github.com/ceph/chacra#chacra"
        projects = [p.name for p in Project.query.all()]
        repo_projects = Project.query.join(Repo).filter(Repo.path != None)
        repos = [p.name for p in repo_projects.all()]
        return dict(
            description=description,
            documentation=documentation,
            repos=repos,
            binaries=projects)

    binaries = ProjectsController()
    errors = ErrorsController()
    search = SearchController()
    repos = RepoProjectsController()
