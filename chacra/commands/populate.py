import os

from pecan.commands.base import BaseCommand
from pecan import conf

from alembic.config import Config
from alembic import command

from chacra import models


def out(string):
    print "==> %s" % string


def get_alembic_config():
    try:
        os.environ['ALEMBIC_CONFIG']
    except KeyError:
        here = os.path.abspath(os.path.dirname(__file__))
        config_path = os.path.abspath(os.path.join(here, '../../alembic.ini'))
        return config_path


class PopulateCommand(BaseCommand):
    """
    Load a pecan environment and initializate the database.
    """

    def run(self, args):
        super(PopulateCommand, self).run(args)
        out("LOADING ENVIRONMENT")
        self.load_app()
        out("BUILDING SCHEMA")
        try:
            out("STARTING A TRANSACTION...")
            models.start()
            models.Base.metadata.create_all(conf.sqlalchemy.engine)
        except:
            models.rollback()
            out("ROLLING BACK... ")
            raise
        else:
            out("COMMITING... ")
            models.commit()
            out("STAMPING INITIAL STATE WITH ALEMBIC... ")
            alembic_cfg = Config(get_alembic_config())
            command.stamp(alembic_cfg, "head")
