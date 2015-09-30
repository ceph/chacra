import pecan
import os
import logging
import subprocess
from chacra.async import app, SQLATask
logger = logging.getLogger(__name__)


@app.task(base=SQLATask)
def create_repo(repo_ids):
    """
    Go create or update repositories with specific IDs.
    """
    from chacra.models import Repo
    directories = ['SRPMS', 'noarch', 'x86_64']
    # get the root path for storing repos
    for _id in repo_ids:
        # TODO: Is it possible we can get an ID that doesn't exist anymore?
        repo = Repo.get(_id)
        project_name = repo.project.name

        # Determine paths for this repository
        root_path = os.path.join(pecan.conf.repos_root, project_name)
        relative_repo_path = '%s/%s/%s/%s' % (project_name, repo.ref, repo.distro, repo.distro_version)
        abs_repo_path = os.path.join(root_path, relative_repo_path)
        repo_dirs = [os.path.join(abs_repo_path, d) for d in directories]

        # does this repo has a path? if so, it exists already, no need to
        # create structure
        if not repo.path or not os.path.exists(repo.path):
            os.path.mkdir(abs_repo_path)
            for d in repo_dirs:
                if not os.path.exists(d):
                    os.mkdir(d)

        # now that structure is done, we need to symlink the RPMs that belong
        # to this repo so that we can create the metadata.
        # FIXME!!! This is just assuming x86_64 for now and slapping everything
        # there which is (or can be) completely incorrect
        for binary in repo.binaries:
            source = binary.path
            destination = os.path.join(abs_repo_path, 'x86_64')
            os.symlink(source, destination)

        for d in repo_dirs:
            subprocess.call(['createrepo', d])
