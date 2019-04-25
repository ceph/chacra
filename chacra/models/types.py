import json
from copy import deepcopy
from sqlalchemy import types as SATypes
from chacra.compat import PY3


class JSONType(SATypes.TypeDecorator):
    impl = SATypes.UnicodeText

    def process_bind_param(self, value, engine):
        if PY3:
            return json.dumps(value)
        else:
            return unicode(json.dumps(value))  # noqa

    def process_result_value(self, value, engine):
        if value:
            return json.loads(value)
        else:
            return {}  # pragma: nocover

    def copy_value(self, value):
        return deepcopy(value)
