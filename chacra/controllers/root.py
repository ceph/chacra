from pecan import expose
from chacra.controllers.projects import ProjectsController


class RootController(object):

    @expose('json')
    def index(self):
        return dict()

    projects = ProjectsController()
