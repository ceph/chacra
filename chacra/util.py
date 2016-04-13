from collections import defaultdict
import os
import errno
import logging
from pecan import conf
from pecan.templating import MakoRenderer, ExtraNamespace

from chacra import models
from chacra.constants import DISTRIBUTIONS

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


def get_related_projects(project, repo_config=None):
    """
    Find out if ``project`` of a given ``ref`` might be needed in repositories
    for other projects (defined via configuration).
    """
    matches = defaultdict(list)
    repo_config = repo_config or getattr(conf, 'repos', {})
    if not repo_config:
        return {}
    for project_name in repo_config.keys():
        project_configuration = repo_config[project_name]
        project_refs = project_configuration.keys()
        for project_ref in project_refs:
            # 'combined' is not a ref, it is an option
            if project_ref == 'combined':
                continue
            ref_configuration = project_configuration[project_ref]
            related_projects = ref_configuration.keys()
            if project in related_projects:
                if project_ref == 'all':
                    matches[project_name] = ['all']
                    # no need to continue because we need to use all
                    # refs
                    break
                else:
                    # otherwise append it, we might have other distinct refs we
                    # care about. Take special care of avoiding a circular
                    # reference by not including the same related project as
                    # the parent one.

                    if project != project_name:
                        matches[project_name].append(project_ref)
    return matches


def get_combined_repos(project, repo_config=None):
    """
    Configuration can define specific project repositories to be
    'combined', this combination of different distro versions are only for
    Debian-based distros and involves some spelunking in the dictionary
    to configure them.

    This helper will always return a list because that is the expectation from
    the configuration.
    """
    repo_config = repo_config or getattr(conf, 'repos', {})
    if not repo_config:
        return []
    return repo_config.get(project, {}).get('combined', [])


def get_extra_repos(project, ref=None, repo_config=None):
    """
    Go through the configuration options for each 'ref' in a project and return
    the matching ref option for a project, falling to 'all' which signals work
    for all (but really 'any' in this case) refs.

    If nothing is defined an empty dictionary is returned, so that consumers
    can treat the return values always as a dictionary
    """
    repo_config = repo_config or getattr(conf, 'repos', {})
    project_ref = ref or 'all'
    if not repo_config:
        logging.debug('no repos configuration defined for extra repositories')
        return {}
    project_config = repo_config.get(project, {})
    if not project_config:
        logging.debug('%s has no configuration for extra repositories', project)
        return {}
    # check first for 'all', if present, process that first:
    all_refs = project_config.get('all', {})
    distinct_ref = {}
    # now check for a distinct ref if we were asked for one:
    if ref is not None:
        distinct_ref = project_config.get(ref, {})

    # now that both have been check, combine them so that they can be processed
    # as one large dictionary, note that key from distinct refs will be
    # overwritten by 'all' refs, that is: 'all' has more importance than
    # distinct, this is assumed as a configuration oversight by the user.
    distinct_ref.update(all_refs)

    if not distinct_ref:
        logger.warning('%s has no matching repositories for ref: %s', project, project_ref)
    return distinct_ref


def get_extra_binaries(project_name, distro, distro_version, distro_versions=None, ref=None):
    """
    Try to match a given repository with the distinctive  project/ref/distro
    information and return a list of associated binaries
    """
    binaries = []
    project = models.Project.query.filter_by(name=project_name).first()
    if not project:
        logger.warning(
            '%s does not exist but is configured, no binaries fetched',
            project_name
        )
        return []
    repo_query = models.Repo.query.filter_by(project=project)

    if distro_versions:
        repo_query = repo_query.filter(models.Repo.distro_version.in_(distro_versions))
    else:
        repo_query = repo_query.filter_by(distro_version=distro_version)

    if distro is not None:
        repo_query = repo_query.filter_by(distro=distro)

    if ref is None:
        # means that we should just get everything that matches our original
        # query as a list
        for r in repo_query.all():
            binaries += [b for b in r.binaries]
    else:
        # further filter by using ref but looking for all matching repos
        for r in repo_query.filter_by(ref=ref).all():
            binaries += [b for b in r.binaries]
    logger.info('%d matched binaries found', len(binaries))
    return binaries


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


def render_mako_template(template_name, data):
    """
    Will render the given mako template and return it as a string.

    The template_name must exist in chacra/templates.
    """
    #TODO: should this path be configurable?
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    engine = MakoRenderer(template_dir, ExtraNamespace())
    return engine.render(template_name, data)


def get_distributions_file_context(project_name):
    """
    Using conf.distributions build the context needed
    to render the project specific distributions file.
    """
    data = dict()
    dist_config = conf.distributions.to_dict()
    data['data'] = dist_config.get('defaults', {})
    project_overrides = dist_config.get(project_name, {})
    data['data'].update(project_overrides)
    data["distributions"] = DISTRIBUTIONS
    return data


def create_distributions_file(project_name, distributions_path):
    """
    Will create a project specific distributions file to be used by reprepo.
    """
    data = get_distributions_file_context(project_name)
    contents = render_mako_template("distributions", data)
    with open(distributions_path, "w") as f:
        try:
            f.write(contents)
        except (OSError, IOError):
            logger.exception('Could not create %s' % distributions_path)
            raise


def reprepro_confdir(project_name):
    """
    Will return the path to an existing project specific configuration directory
    which will contain a distributions file for that project.

    If the configuration directory or distributions file do not exist, they
    will be created.
    """
    confdir_path = os.path.join(conf.distributions_root, project_name)
    distributions_path = os.path.join(confdir_path, "distributions")
    if not os.path.exists(distributions_path):
        makedirs(confdir_path)
    # we need to recreate this everytime to account for changes
    # in the configuration
    create_distributions_file(project_name, distributions_path)

    return confdir_path


def reprepro_command(repository_path, binary, distro_version=None):
    """
    Depending on the filetype we are dealing the reprepro command will need to
    change to accommodate for its inclusion in a DEB repository. This is
    specifically meant to handle both .dsc and .changes files which need to be
    treaded differently.
    """
    distro_version = distro_version or binary.distro_version
    include_flags = {
        'deb': 'includedeb',
        'dsc': 'includedsc',
        'changes': 'include',
    }
    # It is OK to fail so that the KeyError can be catched and properly ignored
    # when adding such an unknown file to the repo
    include_flag = include_flags[binary.extension]
    return [
        'reprepro',
        '--confdir', reprepro_confdir(binary.project.name),
        '-b', repository_path,
        '-C', 'main',
        '--ignore=wrongdistribution',
        '--ignore=wrongversion',
        '--ignore=undefinedtarget',
        include_flag, distro_version,
        binary.path
    ]


def reprepro_commands(repository_path, binary,
        distro_versions=None, fallback_version=None):
    """
    When a generic (non-distro-version-specific) DEB binary is built it can't
    be added with reprepro as-is because internal chacra mechanisms infer the
    distro version of the repo looking into the metadata associated with the
    binary.

    A binary like ceph-deploy_1.5.30_all.deb that lives in a path like
    ceph-deploy/master/debian/universal/all/ will generate a reprepro command
    that attempts to add the binary to a repo using "universal" as the distro
    version, which doesn't exist.

    This is only a problem with generic binaries, so this helper function will
    try to detect this by matching the distro version to a few values allowed
    for generic builds:

    * generic
    * universal
    * any

    Instead of returning a single command (as a list so that it can be consumed
    with Popen) it will return all possible commands if ``distro_versions`` is
    used or just a single item in a list if none are passed.
    """
    if binary.is_generic:
        if not distro_versions:
            if fallback_version:
                distro_versions = [fallback_version]
            else:
                # at this point we don't have either distro_versions or
                # a fallback and the binary is generic which means we will be
                # unable to add it back to the repos, so give up with
                # a warning.
                logger.warning(
                    "%s is generic but no fallback or distro versions where defined"
                )
                logger.warning("no reprepro command will be issued")
                return []
    else:
        # since this is not a generic binary, use its own distro_version to
        # create the reprepro command
        distro_versions = [binary.distro_version]

    commands = []
    for distro_version in distro_versions:
        commands.append(
            reprepro_command(
                repository_path,
                binary,
                distro_version=distro_version
            )
        )
    return commands

def repository_is_disabled(project_name, repo_config=None):
    repo_config = repo_config or getattr(conf, 'repos', {})
    disable_unconfigured_repos = getattr(conf, 'disable_unconfigured_repos', False)
    logger.debug('checking if repository should be disabled for project: %s', project_name)
    if disable_unconfigured_repos:
        logger.debug('repository creation for unconfigured repos is disabled')
        # check if the repo exists in the repo configuration and it is not
        # disabled there
        if repo_config.get(project_name):
            # it exists, but it may be explicitly disabled
            if repo_config[project_name].get('disabled'):
                logger.info('project: %s is explicitly disabled in config, will skip repo creation', project_name)
                return True
            # it exists but it is not explicitly disabled
            else:
                logger.info('project: %s is explicitly enabled in config, repo will be created/updated', project_name)
                return False
        logger.info('project: %s is unconfigured, will skip repo creation', project_name)
        return True
    if repo_config.get(project_name, {}).get('disabled', False):
        logger.info('project: %s is explicitly disabled in config, will skip repo creation', project_name)
        return True
    if not repo_config:
        logger.info('no specific repo configuration found, will create repo for project: %s', project_name)
        return False
    # if unconfigured repos are not disabled and no repo is configured this
    # means this should not be disabled
    return False
