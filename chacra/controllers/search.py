from pecan import expose
from chacra.models import Binary
from chacra.controllers import error


class SearchController(object):

    def __init__(self):
        self.filters = {
                'distro': Binary.distro,
                'distro_version': Binary.distro_version,
                'arch': Binary.arch,
                'ref': Binary.ref,
                'built_by': Binary.built_by,
                'size': Binary.size,
                'name': Binary.name,
                'name-like': Binary.name.like,
        }

    @expose('json')
    def index(self, **kw):
        query = self.apply_filters(kw)
        return query.all()

    def apply_filters(self, filters):
        # TODO: allow operators
        query = None
        for k, v in filters.items():
            if k not in self.filters:
                return error('/errors/not_allowed', 'invalid query params: %s' % k)
            if k in self.filters:
                query = self.filter_binary(self.filters[k], v, query)
        return query

    def filter_binary(self, key, value, query=None):
        if query:
            return query.filter(key == value)
        return Binary.query.filter(key == value)
