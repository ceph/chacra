from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, backref
from chacra.models import Base


class Project(Base):

    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, unique=True, index=True)

    def __init__(self, name):
        self.name = name


    def __json__(self):
        return dict(
            name=self.name,
        )

