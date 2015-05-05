from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref
from chacra.models import Base


class Binary(Base):

    __tablename__ = 'binaries'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, index=True)

    arch_id = Column(Integer, ForeignKey('archs.id'))
    arch = relationship('DistroArch', backref=backref('archs', lazy='dynamic'))

    def __init__(self, name, arch):
        self.name = name
        self.arch = arch

    def last_updated(self):
        # TODO
        pass

    def __json__(self):
        return dict(
            name=self.name,
            versions=self.versions
        )

