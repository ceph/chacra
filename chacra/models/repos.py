import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.event import listen
from sqlalchemy.orm.exc import DetachedInstanceError
from chacra.models import Base, update_timestamp


class Repo(Base):

    __tablename__ = 'repos'
    id = Column(Integer, primary_key=True)
    path = Column(String(256))
    ref = Column(String(256), index=True)
    sha1 = Column(String(256), index=True, default='head')
    distro = Column(String(256), nullable=False, index=True)
    distro_version = Column(String(256), nullable=False, index=True)
    flavor = Column(String(256), nullable=False, index=True, default='default')
    modified = Column(DateTime, index=True)
    signed = Column(Boolean(), default=False)
    needs_update = Column(Boolean(), default=True)
    is_updating = Column(Boolean(), default=False)
    is_queued = Column(Boolean(), default=False)
    type = Column(String(12))
    size = Column(Integer, default=0)

    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship('Project', backref=backref('repos', lazy='dynamic'))

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
            return "<Repo {}/{}/{}/{}/{}>".format(
                self.project.name,
                self.ref,
                self.sha1,
                self.distro,
                self.distro_version,
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
        )

    @property
    def uri(self):
        return "{}/{}/{}/{}/{}/flavors/{}/".format(
            self.project.name,
            self.ref,
            self.sha1,
            self.distro,
            self.distro_version,
            self.flavor,
        )

    @property
    def is_generic(self):
        for binary in self.binaries:
            if binary.is_generic:
                return True
        return False

    @property
    def metric_name(self):
        return "repos.%s.%s.%s.%s" % (
            self.project.name,
            self.ref,
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


# listen for timestamp modifications
listen(Repo, 'before_insert', update_timestamp)
listen(Repo, 'before_update', update_timestamp)
