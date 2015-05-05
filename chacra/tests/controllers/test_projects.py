from chacra.models import Package


class TestPackagesController(object):

    def test_get_index_no_packages(self, session):
        result = session.app.get('/packages/')
        assert result.status_int == 200
        assert result.json == {}

    def test_list_a_project(self, session):
        Package('foobar', 'example.com')
        session.commit()

        result = session.app.get('/packages/')
        json = result.json['packages']
        assert result.status_int == 200
        assert len(json) == 1

    def test_list_a_couple_of_packages(self, session):
        for p in range(20):
            Package('foo_%s' % p, 'example.com')
        session.commit()

        result = session.app.get('/packages/')
        json = result.json['packages']
        assert result.status_int == 200
        assert len(json) == 20

    def test_get_extra_metadata_for_package(self, session):
        Package('foobar', 'example.com')
        session.commit()

        result = session.app.get('/packages/')
        json = result.json['packages']
        last_updated = json['foobar']['last_updated']
        assert last_updated.endswith('seconds ago')


class TestPackageController(object):

    def test_get_index_single_project(self, session):
        Package('foobar', 'example.com')
        result = session.app.get('/packages/foobar/')
        assert result.status_int == 200

    def test_get_index_no_project(self, session):
        result = session.app.get('/packages/foobar/', expect_errors=True)
        assert result.status_int == 404

    def test_get_index_single_project_data(self, session):
        Package('foobar', 'example.com')
        result = session.app.get('/packages/foobar/')
        assert result.json == {}
