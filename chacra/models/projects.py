from sqlalchemy import Column, Integer, String
from sqlalchemy.orm.exc import DetachedInstanceError
from chacra.models import Base


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

    def __repr__(self):
        try:
            return '<Project %r>' % self.name
        except DetachedInstanceError:
            return '<Project detached>'

    def __json__(self):
        return dict(
            refs=self.refs
        )

