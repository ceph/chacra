from pecan import expose, abort

from chacra.async import checks


class HealthController(object):

    @expose('json')
    def index(self):
        if checks.is_healthy():
            return "Everything OK"
        abort(500, "Health check failed.")
