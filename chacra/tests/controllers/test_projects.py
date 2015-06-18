from chacra.models import Project, Binary


class TestProjectsController(object):

    def test_get_index_no_projects(self, session):
        result = session.app.get('/projects/')
        assert result.status_int == 200
        assert result.json == {}

    def test_list_a_project(self, session):
        Project('foobar')
        session.commit()
        result = session.app.get('/projects/')
        assert result.json['foobar']['name'] == 'foobar'

    def test_single_project_should_have_one_item(self, session):
        Project('foobar')
        session.commit()
        result = session.app.get('/projects/')
        assert result.status_int == 200
        assert len(result.json) == 1

    def test_list_a_few_projects(self, session):
        for p in range(20):
            Project('foo_%s' % p)
        session.commit()

        result = session.app.get('/projects/')
        json = result.json
        assert result.status_int == 200
        assert len(json) == 20

# TODO
#    def test_get_extra_metadata_for_package(self, session):
#        Project('foobar')
#        session.commit()
#
#        result = session.app.get('/projects/')
#        last_updated = result.json['foobar']['last_updated']
#        assert last_updated.endswith('seconds ago')


class TestProjectController(object):

    def test_get_index_single_project(self, session):
        Project('foobar')
        session.commit()
        result = session.app.get('/projects/foobar/')
        assert result.status_int == 200

    def test_get_index_no_project(self, session):
        result = session.app.get('/projects/foobar/', expect_errors=True)
        assert result.status_int == 404

    def test_get_index_single_project_data(self, session):
        Project('foobar')
        session.commit()
        result = session.app.get('/projects/foobar/')
        assert result.json == {'name': 'foobar', 'refs': []}

    def test_get_project_refs(self, session):
        p = Project('foobar')
        Binary('ceph-1.0.0.rpm', p, ref='master', distro='centos', distro_version='el6', arch='i386')
        Binary('ceph-1.0.0.rpm', p, ref='firefly', distro='centos', distro_version='el6', arch='i386')
        session.commit()
        result = session.app.get('/projects/foobar/')
        assert result.json == {'name': 'foobar', 'refs': ['firefly', 'master']}
