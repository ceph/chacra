from chacra.models import Project, Distro, DistroVersion


class TestDistroController(object):

    def test_list_a_distro_no_versions(self, session):
        project = Project('ceph')
        Distro('ubuntu', project)
        session.commit()
        result = session.app.get('/projects/ceph/ubuntu/')
        assert result.json == {}

    def test_single_distro_should_have_one_item(self, session):
        project = Project('ceph')
        distro = Distro('ubuntu', project)
        DistroVersion('12.04', distro)
        session.commit()
        result = session.app.get('/projects/ceph/ubuntu/')
        assert result.status_int == 200
        assert len(result.json) == 1

    def test_single_distro_should_have_a_name(self, session):
        project = Project('ceph')
        distro = Distro('ubuntu', project)
        DistroVersion('12.04', distro)
        session.commit()
        result = session.app.get('/projects/ceph/ubuntu/')
        assert result.json['12.04']['name'] == '12.04'
