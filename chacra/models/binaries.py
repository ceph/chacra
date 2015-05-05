import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship, backref
from chacra.models import Base
from chacra.controllers import util


class Binary(Base):

    __tablename__ = 'binaries'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, unique=True, index=True)
    path = Column(String(256))
    built_by = Column(String(256))
    created = Column(DateTime, index=True)
    modified = Column(DateTime, index=True)
    signed = Column(Boolean(), default=False)
    byte_size = Column(Integer, default=0)

    arch_id = Column(Integer, ForeignKey('archs.id'))
    arch = relationship('DistroArch', backref=backref('binaries', lazy='dynamic'))

    allowed_keys = [
        'path',
        'built_by',
        'byte_size',
    ]

    def __init__(self, name, arch, **kw):
        self.name = name
        self.arch = arch
        self.created = datetime.datetime.utcnow()
        self.modified = datetime.datetime.utcnow()
        for key in self.allowed_keys:
            if key in kw.keys():
                setattr(self, key, kw[key])

    def last_updated(self):
        # TODO
        pass

    @property
    def last_changed(self):
        if self.modified > self.created:
            last = self.modified
        else:
            last = self.created
        return util.last_seen(last)

    def __json__(self):
        return dict(
            name=self.name,
            created=self.created,
            modified=self.modified,
            signed=self.signed,
            size=self.byte_size,
            path=self.path,
            last_changed=self.last_changed,
            built_by=self.built_by,
        )

