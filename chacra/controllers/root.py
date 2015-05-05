from pecan import expose
from chacra.controllers.projects import ProjectsController
from chacra.controllers.errors import ErrorsController


class RootController(object):

    @expose('json')
    def index(self):
        return dict()

    projects = ProjectsController()
    errors = ErrorsController()
