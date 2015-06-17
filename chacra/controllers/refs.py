from pecan import expose, abort, request
from chacra.models import projects
from chacra import models
from chacra.controllers import error, set_id_in_context
from chacra.controllers.distros import DistroController


class RefController(object):

    def __init__(self, ref_name):
        self.ref_name = ref_name
        self.ref = models.Ref.query.filter_by(name=ref_name).first()
        if not self.ref:
            if request.method != 'POST':
                abort(404)
            elif request.method == 'POST':
                project = projects.Project.get(request.context['project_id'])
                self.ref = models.get_or_create(models.Ref, name=ref_name, project=project)
        set_id_in_context('ref_id', self.ref, ref_name)

    @expose('json')
    def index(self):
        if request.method == 'POST':
            error('/errors/not_allowed', 'POST requests to this url are not allowed')

        return dict(
            (d.name, d) for d in self.ref.distros.all()
        )

    @expose()
    def _lookup(self, name, *remainder):
        return DistroController(name), remainder
