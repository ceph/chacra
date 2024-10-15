from pecan import expose, abort

from chacra.asynch import checks


class HealthController(object):

    @expose()
    def index(self):
        if not checks.is_healthy():
            abort(500)
