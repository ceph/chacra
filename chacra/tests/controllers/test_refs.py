from chacra.models import Project, Ref, Distro


class TestRefController(object):

    def test_get_index_single_ref(self, session):
        p = Project('ceph')
        Ref('master', p)
        session.commit()
        result = session.app.get('/projects/ceph/master/')
        assert result.status_int == 200

    def test_get_index_no_ref(self, session):
        Project('ceph')
        session.commit()
        result = session.app.get('/projects/ceph/next/', expect_errors=True)
        assert result.status_int == 404

    def test_get_index_single_ref_data(self, session):
        p = Project('ceph')
        r = Ref('master', p)
        Distro('ubuntu', r)
        session.commit()
        result = session.app.get('/projects/ceph/master/')
        assert result.json == {}

