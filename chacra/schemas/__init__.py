from notario.validators import types
from notario.decorators import optional

repo_schema = (
    (optional("distro"), types.string),
    (optional("distro_version"), types.string),
    (optional("needs_update"), types.boolean),
    (optional("ref"), types.string),
    (optional("type"), types.string),
)
