from sqlalchemy import Column, Integer, String
from sqlalchemy.orm.exc import DetachedInstanceError
from chacra.models import Base
from chacra.models.repos import Repo


class Project(Base):

    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, unique=True, index=True)

    def __init__(self, name):
        self.name = name

    @property
    def archs(self):
        return list(set([b.arch for b in self.binaries.all()]))

    @property
    def distro_versions(self):
        return list(set([b.distro_version for b in self.binaries.all()]))

    @property
    def distros(self):
        return list(set([b.distro for b in self.binaries.all()]))

    @property
    def refs(self):
        return list(set([b.ref for b in self.binaries.all()]))

    @property
    def sha1s(self):
        return list(set([b.sha1 for b in self.binaries.all()]))

    @property
    def flavors(self):
        return list(set([b.flavor for b in self.binaries.all()]))

    @property
    def built_repos(self):
        return self.repos.filter(Repo.path != None)

    @property
    def repo_refs(self):
        return list(set([r.ref for r in self.built_repos.all()]))

    @property
    def repo_sha1s(self):
        return list(set([r.sha1 for r in self.built_repos.all()]))

    @property
    def repo_distros(self):
        return list(set([r.distro for r in self.built_repos.all()]))

    @property
    def repo_distro_versions(self):
        return list(set([r.distro_version for r in self.built_repos.all()]))

    def __repr__(self):
        try:
            return '<Project %r>' % self.name
        except DetachedInstanceError:
            return '<Project detached>'

    def __json__(self):
        json_ = {}
        for ref in self.refs:
            json_[ref] = list(
                set(
                    [b.sha1 for b in self.binaries.filter_by(ref=ref).all()]
                )
            )
        return json_


def get_or_create(name, **kw):
    project = Project.filter_by(name=name).first()
    if not project:
        project = Project(name=name)
    return project
