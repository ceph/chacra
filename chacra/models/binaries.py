import hashlib
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, BigInteger
from sqlalchemy.orm import relationship, backref
from sqlalchemy.event import listen
from sqlalchemy.orm.exc import DetachedInstanceError
from sqlalchemy.exc import InvalidRequestError
from chacra.models import Base, update_timestamp
from chacra.models.repos import Repo
from chacra.controllers import util


class Binary(Base):

    __tablename__ = 'binaries'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, index=True)
    path = Column(String(256))
    ref = Column(String(256), index=True)
    sha1 = Column(String(256), index=True, default='head')
    distro = Column(String(256), nullable=False, index=True)
    distro_version = Column(String(256), nullable=False, index=True)
    arch = Column(String(256), nullable=False, index=True)
    flavor = Column(String(256), nullable=False, index=True, default='default')
    built_by = Column(String(256))
    created = Column(DateTime, index=True)
    modified = Column(DateTime, index=True)
    signed = Column(Boolean(), default=False)
    size = Column(BigInteger, default=0)
    checksum = Column(String(256))

    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship('Project', backref=backref('binaries', lazy='dynamic'))

    repo_id = Column(Integer, ForeignKey('repos.id'))
    repo = relationship('Repo', backref=backref('binaries', lazy='dynamic'))

    allowed_keys = [
        'path',
        'distro',
        'distro_version',
        'arch',
        'ref',
        'sha1',
        'built_by',
        'size',
        'flavor',
    ]

    def __init__(self, name, project, repo=None, **kw):
        self.name = name
        self.project = project
        now = datetime.datetime.utcnow()
        self.created = now
        self.modified = now
        self.sha1 = kw.get('sha1', 'head')
        self.flavor = kw.get('flavor', 'default')
        for key in self.allowed_keys:
            if key in kw.keys():
                setattr(self, key, kw[key])
        self.repo = repo or self._get_or_create_repo()
        # ensure that the repo.type is set
        self._set_repo_type()

    @property
    def extension(self):
        return self.name.split('.')[-1]

    def _get_repo_type(self):
        extension_map = {
            'rpm': 'rpm',
            'deb': 'deb',
            'ddeb': 'deb',
            'dsc': 'deb',
            'changes': 'deb'
        }

        # XXX This is very naive, but 'deb' repos are the only ones that
        # will have .tar or .tar.gz or just .gz extensions for source
        # files, so fallback to that
        return extension_map.get(self.extension, 'deb')

    def _set_repo_type(self):
        if self.repo.type is None:
            self.repo.type = self._get_repo_type()

    def _get_or_create_repo(self):
        """
        A repo model object may exist for this binary, if it exists, then
        return it otherwise create it and then return it.
        """
        # try to find one that matches our needs first
        repo = Repo.query.filter_by(
            ref=self.ref,
            sha1=self.sha1,
            flavor=self.flavor,
            distro=self.distro,
            distro_version=self.distro_version,
            project=self.project).first()

        # create one otherwise
        if not repo:
            repo = Repo(
                self.project,
                self.ref,
                self.distro,
                self.distro_version,
                sha1=self.sha1,
                flavor=self.flavor,
                type=self._get_repo_type(),
            )
        # only needs_update when binary is not generic and automatic repos
        # are configured for this project
        repo.needs_update = not self.is_generic and util.repository_is_automatic(self.project.name)
        return repo

    def __repr__(self):
        try:
            return '<Binary %r>' % self.name
        except DetachedInstanceError:
            return '<Binary detached>'

    @property
    def last_changed(self):
        if self.modified > self.created:
            last = self.modified
        else:
            last = self.created
        return util.last_seen(last)

    @property
    def is_generic(self):
        """
        Generic binaries are built without a specific target distribution version. They should
        work in any version/release which requires the repository-creation mechanism to special case
        them as repositories may be combined and require us to add them to different distributions.
        Specifically, we match the distro version to:

        * generic
        * universal
        * any
        """
        target_versions = ['generic', 'universal', 'any']
        if self.distro_version in target_versions:
            return True
        return False

    def __json__(self):
        return dict(
            name=self.name,
            project=self.project.name,
            created=self.created,
            modified=self.modified,
            signed=self.signed,
            size=self.size,
            path=self.path,
            last_changed=self.last_changed,
            built_by=self.built_by,
            distro=self.distro,
            distro_version=self.distro_version,
            checksum=self.checksum,
            arch=self.arch,
            ref=self.ref,
            sha1=self.sha1,
            flavor=self.flavor,
        )


# Listeners


def generate_checksum(mapper, connection, target):
    try:
        target.path
    except AttributeError:
        target.checksum = None
        return

    # FIXME
    # sometimes we can accept binaries without a path and that is probably something
    # that should not happen. The core purpose of this binary is that it works with
    # paths and files, this should be required.
    if not target.path:
        return
    chsum = hashlib.sha512()
    with open(target.path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            chsum.update(chunk)
        target.checksum = chsum.hexdigest()


def update_repo(mapper, connection, target):
    try:
        if target.repo.is_generic:
            return
    except (AttributeError, InvalidRequestError):
        # SQLA might not have finished flushing the object
        # so it really doesn't know if it is a generic one or not
        # so do not update anything
        return
    try:
        if util.repository_is_automatic(target.project.name):
            target.repo.needs_update = True
    except AttributeError:
        # target may be None in certain cases, and we don't care which one
        # triggered it because there is nothing we need to do
        pass

# listen for checksum changes
listen(Binary, 'before_insert', generate_checksum)
listen(Binary, 'before_update', generate_checksum)


# listen for timestamp modifications
listen(Binary, 'before_insert', update_timestamp)
listen(Binary, 'before_update', update_timestamp)


# listen for any changes to mark the repos
listen(Binary, 'before_insert', update_repo)
listen(Binary, 'before_update', update_repo)

