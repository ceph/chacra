from sqlalchemy import Column, Integer, String
from sqlalchemy.orm.exc import DetachedInstanceError
from sqlmodel import Field, SQLModel
from chacra.models import Base
from chacra.models.repos import Repo
from chacra.models.binaries import Binary


class Project(SQLModel, Base, table=True):

    __tablename__ = 'projects'
    id: int = Field(primary_key=True)
    name: str = Field(max_length=256, nullable=False, unique=True, index=True)

    def __init__(self, name):
        self.name = name

    @property
    def archs(self):
        return list(set(
            [b.arch for b in
             Binary.query.distinct(Binary.arch).filter_by(project=self).all()]
        ))

    @property
    def distro_versions(self):
        return list(set(
            [b.distro_version for b in
             Binary.query.distinct(Binary.distro_version).filter_by(project=self).all()]
        ))

    @property
    def distros(self):
        return list(set(
            [b.distro for b in
             Binary.query.distinct(Binary.distro).filter_by(project=self).all()]
        ))

    @property
    def refs(self):
        return list(set(
            [b.ref for b in
             Binary.query.distinct(Binary.ref).filter_by(project=self).all()]
        ))

    @property
    def sha1s(self):
        return list(set(
            [b.sha1 for b in
             Binary.query.distinct(Binary.sha1).filter_by(project=self).all()]
        ))

    @property
    def flavors(self):
        return list(set(
            [b.flavor for b in
             Binary.query.distinct(Binary.flavor).filter_by(project=self).all()]
        ))

    @property
    def built_repos(self):
        return self.repos.filter(Repo.path != None)

    @property
    def repo_refs(self):
        return list(set([r.ref for r in self.repos.all()]))

    @property
    def repo_sha1s(self):
        return list(set([r.sha1 for r in self.repos.all()]))

    @property
    def repo_distros(self):
        return list(set([r.distro for r in self.repos.all()]))

    @property
    def repo_distro_versions(self):
        return list(set([r.distro_version for r in self.repos.all()]))

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
                    [b.sha1 for b in
                     Binary.query.distinct(Binary.sha1).filter_by(ref=ref, project=self).all()]
                )
            )
        return json_


def get_or_create(name, **kw):
    project = Project.filter_by(name=name).first()
    if not project:
        project = Project(name=name)
    return project
