import datetime
import errno
import os
import json
import pecan
import requests
import shutil
from sqlalchemy import desc
from celery import shared_task
from chacra import models
from chacra.async import base, debian, rpm, post_queued, post_deleted
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
            post_queued(r)
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


@shared_task(base=base.SQLATask)
def purge_repos(_now=None):
    """
    Purge built repositories, including the associated model objects.
    """
    if getattr(pecan.conf, 'purge_repos', False) is False:
        logger.info('purge_repos option is unset or explicitly disabled, will skip purge')
        return

    # default value for repo life
    now = _now or datetime.datetime.utcnow()
    default_lifespan = now - datetime.timedelta(days=14)
    default_keep_minimum = 0

    purge_rotation = pecan.conf.get('purge_rotation', {})
    # 'all' is a special key to alter defaults for every other project. Not implemented yet.
    purge_projects = [i for i in purge_rotation.keys() if i != 'all']

    logger.info('polling repos for purging....')

    # process configured repos for purging first
    for project_name in purge_projects:
        # set the base query to filter
        p = models.Project.filter_by(name=project_name).first()
        project_repos = models.Repo.filter_by(project=p)

        # get the configuration for current project
        purge_project_config = purge_rotation.get(project_name)

        logger.info('purge_project_config is: %r ', purge_project_config)

        # flavor AND ref are being purged for project
        if(len(purge_project_config.items()) > 1):

            flavors = purge_project_config.get('flavor')
            refs = purge_project_config.get('ref')

            for flavor in flavors:
                flavor_attr = flavors[flavor]

                flavor_days = flavor_attr.get('days', None)
                flavor_keep_minimum = flavor_attr.get('keep_minimum', 0)

                for ref in refs:
                    ref_attr = refs[ref]

                    ref_days = ref_attr.get('days', None)
                    ref_keep_minimum = ref_attr.get('keep_minimum', 0)

                    # in case days was not set in either flavor or ref
                    days = ref_days
                    if flavor_days is None:
                        if ref_days is None:
                            days = 14
                    elif flavor_days >= ref_days:
                        days = flavor_days
                    else:
                        days = ref_days

                    lifespan = now - datetime.timedelta(days=days)

                    if flavor_keep_minimum >= ref_keep_minimum:
                        keep_minimum = flavor_keep_minimum
                    else:
                        keep_minimum = ref_keep_minimum

                    logger.info('ref for this purge is: %r ', ref)
                    logger.info('flavor for this purge is: %r ', flavor)
                    logger.info('keep_minimum for this purge is: %r ', keep_minimum)
                    logger.info('days for this purge is: %r ', days)
                    logger.info('lifespan for this purge is: %r ', lifespan)

                    attr_repos = project_repos.filter_by(flavor=flavor, ref=ref)
                    repos = attr_repos.filter(
                            models.Repo.modified < lifespan).order_by(
                                desc(models.Repo.modified)).offset(keep_minimum).all()

                    logger.info('repos for this purge is: %r ', repos)
                    delete_repositories(repos, lifespan, keep_minimum)

        # flavor OR ref are being purged for project
        else:
            for proj_filter, repo_attrs in purge_project_config.items():
                for attr in repo_attrs:
                    purge_attr = repo_attrs[attr]
                    lifespan = now - datetime.timedelta(days=purge_attr.get('days', 14))
                    keep_minimum = purge_attr.get('keep_minimum', 0)
                    # add similar conditional to filter_by other repo attributes
                    if proj_filter == 'ref':
                        attr_repos = project_repos.filter_by(ref=attr)
                    elif proj_filter == 'flavor':
                        attr_repos = project_repos.filter_by(flavor=attr)
                    repos = attr_repos.filter(
                            models.Repo.modified < lifespan).order_by(
                                desc(models.Repo.modified)).offset(keep_minimum).all()
                    delete_repositories(repos, lifespan, keep_minimum)

    # process everything else that isn't configured, with the defaults
    for r in models.Repo.query.filter(models.Repo.modified < default_lifespan).all():
        # add similar conditional to filter_by other repo attributes
        if purge_rotation.get(r.project.name, {}).get('ref', {}).get(r.ref):
            # this project has a ref with special configuration for purging
            continue
        elif purge_rotation.get(r.project.name, {}).get('flavor', {}).get(r.flavor):
            # this project has a flavor with special configuration for purging
            continue
        delete_repositories([r], default_lifespan, default_keep_minimum)
    logger.info('completed repo purging')


def delete_repositories(repo_objects, lifespan, keep_minimum):
    logger.info('processing deletion for repos %s days and older', lifespan)
    if keep_minimum:
        logger.info('will keep at most %s repositories after purging', keep_minimum)
    else:
        logger.info('will not keep any repositories after purging is completed')

    for r in repo_objects:
        logger.info('repo %s is being processed for removal', r)
        for b in r.binaries:
            try:
                os.remove(b.path)
            except OSError as err:
                # no such file, ignore
                if err.errno == errno.ENOENT:
                    pass
            b.delete()
            models.flush()
        try:
            if r.path:
                shutil.rmtree(r.path)
        except OSError as err:
            # no such file, ignore
            if err.errno == errno.ENOENT:
                pass
            else:
                raise
        post_deleted(r)
        r.delete()
        models.commit()


@shared_task(acks_late=True, bind=True, default_retry_delay=30)
def callback(self, data, project_name, url=None):
    """
    Send a callback to a remote HTTP service. Useful in cases where it is
    needed to advertise the current state of building repositories (since it is
    a time consuming process).

    ``data`` Can be an encoded JSON string or a dictionary. If using specialty
    fields like datetime values, it is safer to use `pecan.jsonify.encode` to
    serialize properly.

    ``acks_late`` will wait until after the task has been acknowledged (not
    before, which is the default) giving a more robust behavior along with
    retrying.

    There is no ``max_retries`` explicitly set because the default (retry
    3 times) is good enough.

    ``default_retry_delay`` is changed to 30 seconds. The default is 3 minutes
    which is too long for this callback.

    .. note:: The use of ``self`` is odd for a function, but this is achieved
    byt the ``bind=True`` so that this task gets access to the task type
    instance

    More detailed information can be found at:

    http://docs.celeryproject.org/en/latest/userguide/tasks.html#retrying
    """
    if url is None:
        if not getattr(pecan.conf, "callback_url", False):
            return
        url = os.path.join(pecan.conf.callback_url, project_name, '')
    headers = {'Content-type': 'application/json'}
    logger.debug('callback for url: %s', url)
    try:
        user = pecan.conf.callback_user
        key = pecan.conf.callback_key
    except AttributeError:
        logger.exception('callback authentication information missing')
        return False

    verify_ssl = getattr(pecan.conf, "callback_verify_ssl", True)

    if isinstance(data, dict):
        try:
            data = json.dumps(data)
        except TypeError:
            logger.exception('could not serialize data')
            return False
    try:
        response = requests.post(
            url,
            data=data,
            auth=(user, key),
            verify=verify_ssl,
            headers=headers
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning('callback failed: %s', str(exc))
        raise self.retry(exc=exc)
    except Exception:
        # Celery eats exceptions for breakfast
        logger.exception('fatal error trying to POST callback')
