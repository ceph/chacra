import os
import errno
import logging
from pecan import conf

logger = logging.getLogger(__name__)


def infer_arch_directory(rpm_binary):
    """
    There has to be a better way to do this. The problem here is that chacra
    URLs are up to the client to define. So if a client POSTs using amd64 as
    the architecture of an RPM binary and this service assumed that amd64 is
    the right architecture the repository structure would then be completely
    incorrect. The right directory name for such a binary would be x86_64.

    Similarly, for 'all' or 'no architecture' binaries, the convention
    dictates a directory should be named 'noarch' (all in lower case). This
    helper method should infer what directory should be used, falling back
    to 'noarch' if it cannot determine what to do with a binary.

    If there is a better way to infer the architecture then this should be
    fixed here.
    """
    name = rpm_binary.lower()
    if name.endswith('src.rpm'):
        return 'SRPMS'
    elif name.endswith('x86_64.rpm'):
        return 'x86_64'
    elif 'noarch' in name.lower():
        return 'noarch'
    return 'noarch'


def repo_paths(repo):
    """
    A helper to construct all the paths that might be useful when
    working with a repository.
    """
    paths = {}

    # e.g. ceph-deploy/master/ubuntu/trusty
    paths['relative'] = '%s/%s/%s' % (
        repo.ref,
        repo.distro,
        repo.distro_version
    )

    # e.g. /opt/repos/ceph-deploy
    paths['root'] = os.path.join(conf.repos_root, repo.project.name)

    paths['absolute'] = os.path.join(paths['root'], paths['relative'])

    return paths


def makedirs(path):
    """
    Check if ``path`` exists, if it does, then don't do anything, otherwise
    create all the intermidiate directories.

    Does not do anything with permissions because that should've been ensured
    with config management.

    On successful creation it will return the path, but this is merely for
    testing purposes and has no effect on behavior.
    """
    try:
        os.makedirs(path)
        return path
    except OSError, e:
        if e.errno == errno.EEXIST:
            pass
        else:
            logger.exception('could not create %s')
            raise
