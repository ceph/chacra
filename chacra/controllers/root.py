from pecan import expose
from chacra.controllers.projects import ProjectsController
from chacra.controllers.errors import ErrorsController
from chacra.controllers.search import SearchController
from chacra.models import Project


description = """chacra is a binary API that allows querying, posting,
updating, and retrieving binaries for different projects."""


class RootController(object):

    @expose('json')
    def index(self):
        documentation = "https://github.com/alfredodeza/chacra#chacra"
        projects = [p.name for p in Project.query.all()]
        return dict(
            description=description,
            documentation=documentation,
            projects=projects)

    projects = ProjectsController()
    errors = ErrorsController()
    search = SearchController()
