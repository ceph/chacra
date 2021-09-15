import celery
from chacra import models


class SQLATask(celery.Task):
    """
    An abstract Celery Task that ensures that the connection the the
    database is closed on task completion

    .. note:: On logs, it may appear as there are errors in the transaction but
    this is not an error condition: SQLAlchemy rolls back the transaction if no
    change was done.
    """
    abstract = True

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        models.clear()


