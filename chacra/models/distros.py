from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref
from chacra.models import Base


class Distro(Base):

    __tablename__ = 'distros'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, index=True)

    ref_id = Column(Integer, ForeignKey('refs.id'))
    ref = relationship('Ref', backref=backref('distros', lazy='dynamic'))

    def __init__(self, name, ref):
        self.name = name
        self.ref = ref

    def last_updated(self):
        # TODO
        pass

    def __json__(self):
        return dict(
            name=self.name,
            versions=self.versions.all()
        )


class DistroVersion(Base):

    __tablename__ = 'versions'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, index=True)

    distro_id = Column(Integer, ForeignKey('distros.id'))
    distro = relationship('Distro', backref=backref('versions', lazy='dynamic'))

    def __init__(self, name, distro):
        self.name = name
        self.distro = distro

    def last_updated(self):
        # TODO
        pass

    def __json__(self):
        return dict(
            name=self.name,
            archs=self.archs.all()
        )


class DistroArch(Base):

    __tablename__ = 'archs'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, index=True)

    version_id = Column(Integer, ForeignKey('versions.id'))
    version = relationship('DistroVersion', backref=backref('archs', lazy='dynamic'))

    def __init__(self, name, version):
        self.name = name
        self.version = version

    def get_binary(self, name):
        for i in self.binaries:
            if i.name == name:
                return i

    def __json__(self):
        return dict(
            name=self.name,
            binaries=self.binaries.all()
        )

