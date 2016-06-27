import pecan
from celery import shared_task
from chacra import models
from chacra.async import base, debian, rpm
import logging
logger = logging.getLogger(__name__)


@shared_task(base=base.SQLATask)
def poll_repos():
    """
    Poll the repository objects that need to be updated and call the tasks
    that can create (or update) repositories with that information

    """
    logger.info('polling repos....')
    for r in models.Repo.query.filter_by(needs_update=True, is_queued=False).all():
        # this repo is being processed, do not pile up and try to get it
        # processed again until it is done doing work
        if r.is_updating:
            continue
        if r.needs_update:
            logger.info("repo %s needs to be updated/created", r)
            r.is_queued = True
            if r.type == 'rpm':
                rpm.create_rpm_repo.apply_async(
                    (r.id,),
                    countdown=pecan.conf.quiet_time,
                    queue='build_repos',
                    )
            elif r.type == 'deb':
                debian.create_deb_repo.apply_async(
                    (r.id,),
                    countdown=pecan.conf.quiet_time,
                    queue='build_repos',
                    )
            else:
                _type = r.infer_type()
                if _type is None:
                    logger.warning('failed to infer repository type')
                    logger.warning('got a repository with an unknown type: %s', r)
                else:
                    logger.warning('inferred repo type as: %s', _type)
                    r.type = _type

            models.commit()

    logger.info('completed repo polling')
