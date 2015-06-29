from pecan import expose
from chacra.controllers.projects import ProjectsController
from chacra.controllers.errors import ErrorsController
from chacra.controllers.search import SearchController


class RootController(object):

    @expose('json')
    def index(self):
        return dict()

    projects = ProjectsController()
    errors = ErrorsController()
    search = SearchController()
