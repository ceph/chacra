from __future__ import print_function
import os
from pecan.testing import load_test_app

import subprocess

from copy import deepcopy
from pecan import conf
from pecan import configuration
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from chacra import models as _db
from chacra.tests import util
import pytest


DBNAME = 'chacratest'
BIND = 'postgresql+psycopg2://'
# for sqlite, use something like this (DBNAME is the name of the file)
# DBNAME = 'chacratest.db'
# BIND = 'sqlite://'


def config_file():
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(here, 'config.py')


def reload_config():
    from pecan import configuration
    config = configuration.conf_from_file(config_file()).to_dict()

    # Add the appropriate connection string to the app config.
    config['sqlalchemy'] = {
        'url': '%s/%s' % (BIND, DBNAME),
        'encoding': 'utf-8',
        'poolclass': NullPool
    }

    configuration.set_config(
        config,
        overwrite=True
    )
    _db.init_model()


@pytest.fixture
def fake():
    class Fake(object):
        def __init__(self, *a, **kw):
            for k, v, in kw.items():
                setattr(self, k, v)
    return Fake

@pytest.fixture
def recorder():
    class Recorder(object):
        def __init__(self, *a, **kw):
            self.recorder_init_call = []
            self.recorder_calls = []
            for k, v, in kw.items():
                setattr(self, k, v)
            self.recorder_init_call.append(
                {'args': a, 'kwargs': kw}
            )
        def __call__(self, *a, **kw):
            for k, v, in kw.items():
                setattr(self, k, v)
            self.recorder_calls.append(
                {'args': a, 'kwargs': kw}
            )

    return Recorder

def pytest_collectstart(collector):
    import os
    os.environ['PECAN_CONFIG'] = config_file()


@pytest.fixture(scope='session')
def app(request):
    config = configuration.conf_from_file(config_file()).to_dict()

    # Add the appropriate connection string to the app config.
    config['sqlalchemy'] = {
        'url': '%s/%s' % (BIND, DBNAME),
        'encoding': 'utf-8',
        'poolclass': NullPool
    }

    # Set up a fake app
    app = TestApp(load_test_app(config))
    return app


@pytest.fixture(scope='session')
def connection(app, request):
    """Session-wide test database."""
    # Connect and create the temporary database
    print("=" * 80)
    print("CREATING TEMPORARY DATABASE FOR TESTS")
    print("=" * 80)
    if BIND.startswith('postgresql'):
        subprocess.call(['dropdb', DBNAME])
        subprocess.call(['createdb', DBNAME])

    # Bind and create the database tables
    _db.clear()
    engine_url = '%s/%s' % (BIND, DBNAME)

    db_engine = create_engine(
        engine_url,
        encoding='utf-8',
        poolclass=NullPool)

    # AKA models.start()
    _db.Session.bind = db_engine
    _db.metadata.bind = _db.Session.bind

    _db.Base.metadata.create_all(db_engine)
    _db.commit()
    _db.clear()

    def teardown():
        _db.Base.metadata.drop_all(db_engine)

    request.addfinalizer(teardown)

    # Slap our test app on it
    _db.app = app
    return _db


@pytest.fixture(scope='function')
def session(connection, request):
    """Creates a new database session for a test."""
    _config = configuration.conf_from_file(config_file()).to_dict()
    config = deepcopy(_config)

    # Add the appropriate connection string to the app config.
    config['sqlalchemy'] = {
        'url': '%s/%s' % (BIND, DBNAME),
        'encoding': 'utf-8',
        'poolclass': NullPool
    }

    connection.start()

    def teardown():

        # Tear down and dispose the DB binding
        connection.clear()

        # start a transaction
        engine = conf.sqlalchemy.engine
        conn = engine.connect()
        trans = conn.begin()


        # gather all data first before dropping anything.
        # some DBs lock after things have been dropped in
        # a transaction.
        if BIND.startswith('postgresql'):
            conn.execute("TRUNCATE TABLE %s RESTART IDENTITY CASCADE" % (
                ', '.join(engine.table_names())
            ))
        elif BIND.startswith('sqlite'):
            for table in engine.table_names():
                conn.execute("DELETE FROM %s" % table)

        trans.commit()
        conn.close()

    request.addfinalizer(teardown)
    return connection


class TestApp(object):
    """
    A controller test starts a database transaction and creates a fake
    WSGI app.
    """

    __headers__ = {}

    def __init__(self, app):
        self.app = app

    def _do_request(self, url, method='GET', **kwargs):
        methods = {
            'GET': self.app.get,
            'POST': self.app.post,
            'POSTJ': self.app.post_json,
            'PUT': self.app.put,
            'HEAD': self.app.head,
            'DELETE': self.app.delete
        }
        kwargs.setdefault('headers', {}).update(self.__headers__)
        return methods.get(method, self.app.get)(str(url), **kwargs)

    def post_json(self, url, **kwargs):
        """
        @param (string) url - The URL to emulate a POST request to
        @returns (paste.fixture.TestResponse)
        """
        # support automatic, correct authentication if not specified otherwise
        if not kwargs.get('headers'):
            kwargs['headers'] = {'Authorization': util.make_credentials()}
        return self._do_request(url, 'POSTJ', **kwargs)

    def post(self, url, **kwargs):
        """
        @param (string) url - The URL to emulate a POST request to
        @returns (paste.fixture.TestResponse)
        """
        # support automatic, correct authentication if not specified otherwise
        if not kwargs.get('headers'):
            kwargs['headers'] = {'Authorization': util.make_credentials()}
        return self._do_request(url, 'POST', **kwargs)

    def get(self, url, **kwargs):
        """
        @param (string) url - The URL to emulate a GET request to
        @returns (paste.fixture.TestResponse)
        """
        return self._do_request(url, 'GET', **kwargs)

    def put(self, url, **kwargs):
        """
        @param (string) url - The URL to emulate a PUT request to
        @returns (paste.fixture.TestResponse)
        """
        if not kwargs.get('headers'):
            kwargs['headers'] = {'Authorization': util.make_credentials()}
        return self._do_request(url, 'PUT', **kwargs)

    def delete(self, url, **kwargs):
        """
        @param (string) url - The URL to emulate a DELETE request to
        @returns (paste.fixture.TestResponse)
        """
        if not kwargs.get('headers'):
            kwargs['headers'] = {'Authorization': util.make_credentials()}
        return self._do_request(url, 'DELETE', **kwargs)

    def head(self, url, **kwargs):
        """
        @param (string) url - The URL to emulate a HEAD request to
        @returns (paste.fixture.TestResponse)
        """
        if not kwargs.get('headers'):
            kwargs['headers'] = {'Authorization': util.make_credentials()}
        return self._do_request(url, 'HEAD', **kwargs)
