import pecan
import os
from chacra.models import Project, Binary


class TestSearchController(object):

    def test_search_by_distro_gets_one_item(self, session):
        project = Project('ceph')
        Binary('ceph-1.0.0.rpm', project, ref='giant', distro='centos', distro_version='el6', arch='x86_64')
        session.commit()
        result = session.app.get('/search/?distro=centos')
        assert len(result.json) == 1

    def test_search_by_distro_gets_no_items(self, session):
        project = Project('ceph')
        Binary('ceph-1.0.0.rpm', project, ref='giant', distro='centos', distro_version='el6', arch='x86_64')
        session.commit()
        result = session.app.get('/search/?distro=solaris')
        assert len(result.json) == 0

    def test_search_by_distro_gets_full_metadata(self, session):
        project = Project('ceph')
        Binary('ceph-1.0.0.rpm', project, ref='giant', distro='centos', distro_version='el6', arch='x86_64')
        session.commit()
        result = session.app.get('/search/?distro=centos').json[0]
        assert result['name'] == 'ceph-1.0.0.rpm'
        assert result['distro'] == 'centos'
        assert result['distro_version'] == 'el6'
        assert result['arch'] == 'x86_64'
        assert result['ref'] == 'giant'

    def test_search_by_distro_gets_more_than_one_item(self, session):
        project = Project('ceph')
        Binary('ceph-1.0.0.rpm', project, ref='giant', distro='centos', distro_version='el6', arch='x86_64')
        Binary('ceph-1.0.0.rpm', project, ref='giant', distro='centos', distro_version='el7', arch='x86_64')
        session.commit()
        result = session.app.get('/search/?distro=centos')
        assert len(result.json) == 2
