from chacra.models import Project, Ref, Distro


class TestRefController(object):

    def test_get_index_single_ref(self, session):
        p = Project('ceph')
        Ref('master', p)
        session.commit()
        result = session.app.get('/projects/ceph/master/')
        assert result.json == {}

    def test_get_index_no_ref(self, session):
        Project('ceph')
        session.commit()
        result = session.app.get('/projects/ceph/next/', expect_errors=True)
        assert result.status_int == 404

    def test_get_index_ref_with_distro(self, session):
        p = Project('ceph')
        r = Ref('master', p)
        Distro('centos', r)
        session.commit()
        result = session.app.get('/projects/ceph/master/')
        assert result.json['centos'] == {'name': 'centos', 'versions': []}

    def test_get_index_ref_with_distros(self, session):
        p = Project('ceph')
        r = Ref('master', p)
        Distro('ubuntu', r)
        Distro('centos', r)
        session.commit()
        result = session.app.get('/projects/ceph/master/')
        assert result.json.keys() == ['centos', 'ubuntu']
