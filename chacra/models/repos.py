import datetime
import os
import socket
from pecan import conf
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.event import listen, remove
from sqlalchemy.orm.exc import DetachedInstanceError
from sqlmodel import Column, Field, SQLModel
from chacra.models import Base, update_timestamp
from chacra.models.types import JSONType


class Repo(SQLModel, Base, table=True):

    __tablename__ = 'repos'
    id: int = Field(primary_key=True)
    path: str | None = Field(max_length=256, default=None)
    ref: str | None = Field(max_length=256, default=None, index=True)
    sha1: str = Field(max_length=256, index=True, default='head')
    distro: str = Field(max_length=256, nullable=False, index=True)
    distro_version: str = Field(max_length=256, nullable=False, index=True)
    flavor: str = Field(max_length=256, nullable=False, index=True, default='default')
    modified: datetime.datetime = Field(default_factory=lambda: datetime.datetime.utcnow())
    signed: bool = Field(default=False)
    needs_update: bool = Field(default=True)
    is_updating: bool = Field(default=False)
    is_queued: bool = Field(default=False)
    type: str | None = Field(default=None)
    size: int = Field(default=0)
    #extra: dict = Field(default={})

    #project_id = Column(Integer, ForeignKey('projects.id'))
    #project = relationship('Project', backref=backref('repos', lazy='dynamic'))

    def __init__(self, project, ref, distro, distro_version, **kwargs):
        self.project = project
        self.ref = ref
        self.distro = distro
        self.distro_version = distro_version
        self.modified = datetime.datetime.utcnow()
        self.sha1 = kwargs.get('sha1', 'head')
        self.flavor = kwargs.get('flavor', 'default')

    def __repr__(self):
        try:
            return "<Repo {name}/{ref}/{sha1}/{distro}/{version}>".format(
                name=self.project.name,
                ref=self.ref,
                sha1=self.sha1,
                distro=self.distro,
                version=self.distro_version,
            )
        except DetachedInstanceError:
            return '<Repo detached>'

    def __json__(self):
        return dict(
            path=self.path,
            project_name=self.project.name,
            ref=self.ref,
            sha1=self.sha1,
            distro=self.distro,
            distro_version=self.distro_version,
            modified=self.modified,
            signed=self.signed,
            needs_update=self.needs_update,
            is_updating=self.is_updating,
            is_queued=self.is_queued,
            type=self.type,
            size=self.size,
            flavor=self.flavor,
            archs=self.archs,
            extra=self.extra,
        )

    @property
    def uri(self):
        return "{name}/{ref}/{sha1}/{distro}/{version}/flavors/{flavor}/".format(
            name=self.project.name,
            ref=self.ref,
            sha1=self.sha1,
            distro=self.distro,
            version=self.distro_version,
            flavor=self.flavor,
        )

    @property
    def base_url(self):
        hostname = getattr(conf, 'hostname', socket.gethostname())
        host_url = 'https://%s/' % hostname
        return os.path.join(host_url, 'r', self.uri, '')

    @property
    def is_generic(self):
        for binary in self.binaries:
            if binary.is_generic:
                return True
        return False

    @property
    def metric_name(self):
        return "repos.%s.%s.%s" % (
            self.project.name,
            self.distro,
            self.distro_version,
        )

    def infer_type(self):
        """
        Sometimes a repo may not know what 'type' it is (a deb or rpm)
        so this goes looking at its binaries for an answer
        """
        for binary in self.binaries:
            return binary._get_repo_type()

    @property
    def archs(self):
        return list(set(b.arch for b in self.binaries))

def add_timestamp_listeners():
    # listen for timestamp modifications
    listen(Repo, 'before_insert', update_timestamp)
    listen(Repo, 'before_update', update_timestamp)

def remove_timestamp_listeners():
    remove(Repo, 'before_insert', update_timestamp)
    remove(Repo, 'before_update', update_timestamp)

add_timestamp_listeners()
