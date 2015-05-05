from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from chacra.models import Base


class Ref(Base):

    __tablename__ = 'refs'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, unique=True, index=True)

    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship('Project', backref=backref('refs', lazy='dynamic'))

    def __init__(self, name, project):
        self.name = name
        self.project = project

    def __json__(self):
        return dict(
            name=self.name,
        )

