from chacra.models import Project, Binary


class TestProjectsController(object):

    def test_get_index_no_projects(self, session):
        result = session.app.get('/binaries/')
        assert result.status_int == 200
        assert result.json == {}

    def test_list_a_project(self, session):
        Project('foobar')
        session.commit()
        result = session.app.get('/binaries/').json
        assert result == {'foobar': []}

    def test_single_project_should_have_one_item(self, session):
        Project('foobar')
        session.commit()
        result = session.app.get('/binaries/')
        assert result.status_int == 200
        assert len(result.json) == 1

    def test_list_a_few_projects(self, session):
        for p in range(20):
            Project('foo_%s' % p)
        session.commit()

        result = session.app.get('/binaries/')
        json = result.json
        assert result.status_int == 200
        assert len(json) == 20

    def test_create_project(self, session):
        session.app.post('/binaries/rhcs-ceph/')
        result = session.app.get('/binaries/rhcs-ceph/')
        assert result.status_int == 200
        assert result.json == {}


class TestProjectController(object):

    def test_get_index_single_project(self, session):
        Project('foobar')
        session.commit()
        result = session.app.get('/binaries/foobar/')
        assert result.status_int == 200

    def test_get_index_no_project(self, session):
        result = session.app.get('/binaries/foobar/', expect_errors=True)
        assert result.status_int == 404

    def test_get_index_single_project_data(self, session):
        Project('foobar')
        session.commit()
        result = session.app.get('/binaries/foobar/')
        assert result.json == {}

    def test_get_project_refs(self, session):
        p = Project('foobar')
        Binary('ceph-1.0.0.rpm', p, ref='main', sha1="HEAD", distro='centos', distro_version='el6', arch='i386')
        Binary('ceph-1.0.0.rpm', p, ref='firefly', sha1="HEAD", distro='centos', distro_version='el6', arch='i386')
        session.commit()
        result = session.app.get('/binaries/foobar/')
        assert result.json == {'firefly': ['HEAD'], 'main': ['HEAD']}
