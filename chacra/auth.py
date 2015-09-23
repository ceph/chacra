import base64
from pecan import request, abort, response, conf


def basic_auth():
    try:
        auth = request.headers.get('Authorization')
        assert auth
        decoded = base64.b64decode(auth.split(' ')[1])
        username, password = decoded.split(':')

        assert username == conf.api_user
        assert password == conf.api_key
    except:
        response.headers['WWW-Authenticate'] = 'Basic realm="Chacra :: Binary API"'
        abort(401)

    return True
