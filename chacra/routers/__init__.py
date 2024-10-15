from os import path
from pecan import request, redirect


def error(url, msg=None):
    if msg:
        request.context['error_message'] = msg
    url = path.join(url, '?error_message=%s' % msg)
    redirect(url, internal=True)


def set_id_in_context(name, object_model, value):
    # if the object_model is None, then it will save it as None
    # saving us from having to do this everywhere
    object_name = name.split('_id')[0]
    if object_model is not None:
        request.context[name] = object_model.id
        request.context[object_name] = object_model.name
    else:
        request.context[name] = None
        request.context[object_name] = value
