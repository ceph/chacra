import os
from pecan.deploy import deploy


def config_file(file_name=None):
    file_name = file_name or 'config.py'
    _file = os.path.abspath(__file__)
    dirname = lambda x: os.path.dirname(x)
    parent_dir = dirname(dirname(_file))
    return os.path.join(parent_dir, file_name)


def application(environ, start_response):
    wsgi_app = deploy(config_file('prod.py'))
    return wsgi_app(environ, start_response)

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    # at some point, it would be nice to use pecan_mount
    #import pecan_mount
    #httpd = make_server('', 8181, pecan_mount.tree)
    httpd = make_server('', 8181, deploy(config_file('config.py')))
    print "Serving HTTP on port 8181..."

    # Respond to requests until process is killed
    httpd.serve_forever()
