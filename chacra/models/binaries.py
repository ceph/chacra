from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship, backref
from chacra.models import Base


class Binary(Base):

    __tablename__ = 'binaries'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, index=True)
    created = Column(DateTime, index=True)
    signed = Column(Boolean(), default=False)
    byte_size = Column(Integer, default=0)

    arch_id = Column(Integer, ForeignKey('archs.id'))
    arch = relationship('DistroArch', backref=backref('binaries', lazy='dynamic'))

    def __init__(self, name, arch):
        self.name = name
        self.arch = arch

    def last_updated(self):
        # TODO
        pass

    def __json__(self):
        return dict(
            name=self.name,
            created=self.created,
            signed=self.signed,
            size=self.byte_size
        )

