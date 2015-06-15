from pecan.commands.base import BaseCommand
from pecan import conf

from chacra import models
from datetime import datetime
import os
import requests
import json


def out(string):
    print "==> %s" % string


def timestamp():
    return datetime.utcnow()


class CrawlCommand(BaseCommand):
    """
    Go through a distinct path looking for binaries and push them
    to the API
    This might be super custom to finding things in file repositories
    """
    arguments = BaseCommand.arguments + (dict(
        name="--type",
        help="rpm or deb, so that this tool understand a bit better how to crawl the paths",  # noqa
    ),
    dict(
        name="--ref",
        help="what 'ref' should be used for this? (e.g. master)",  # noqa
    ),
    dict(
        name="--distro",
        help="what 'distro' should be used for this? (e.g. centos)",  # noqa
    ),
    dict(
        name="--version",
        help="what 'version' of that distro should be used for this? (e.g. squeeze)",  # noqa
    ),
    dict(
        name="--arch",
        help="what 'architecture' should be used for this? (e.g. noarch)",  # noqa
    ),
    dict(
        name="--has",
        help="the string match to find a specific string in filename (e.g. 'bpo60')",  # noqa
    ),
    dict(
        name="--endswith",
        help="the string match to find a specific file.endswith (e.g. '_all.deb')",  # noqa
    ),
    dict(
        name="--project",
        help="the string match to find a specific file.startswith (e.g. 'ceph')",  # noqa
    ),
    dict(
        name="--startswith",
        help="the string match to find a specific file.startswith (e.g. 'ceph')",  # noqa
    ),
    dict(
        name="path",
        help="the path to go for",  # noqa
    ),
    )

    def run(self, args):
        """
        For deb like packages it would be something like::

            ubuntu@jenkins:~/repos/debian-giant$ find . | grep ceph-deploy
            ./pool/main/c/ceph-deploy
            ./pool/main/c/ceph-deploy/ceph-deploy_1.5.11quantal_all.deb
            ./pool/main/c/ceph-deploy/ceph-deploy_1.5.11quantal.tar.gz
            ./pool/main/c/ceph-deploy/ceph-deploy_1.5.11quantal.dsc
            ./pool/main/c/ceph-deploy/ceph-deploy_1.5.18trusty_all.deb

        And some interpretations:

        * _all means the arch is like noarch in rpm-land
        * bpo70 means wheezy
        * bpo60 means squeeze
        """
        super(CrawlCommand, self).run(args)

        if not all((args.distro, args.version, args.arch, args.project, args.ref)):
            raise SystemExit('--project, --ref, --distro, --version, and --arch are required')

        host = conf.server['host']
        port = conf.server['port']
        base_url = 'http://%s:%s/projects/%s/%s/%s/%s/%s/' % (host, port, args.project, args.ref, args.distro, args.version, args.arch)
        print base_url

        # Local is faster
        walk = os.walk
        join = os.path.join
        path = args.path
        levels_deep = 0
        binaries = {}
        for root, dirs, files in walk(path):
            levels_deep += 1

            for item in files:
                absolute_path = join(root, item)
                # checks
                if self.is_valid(item, args):
                    # we have what it looks like a valid binary
                    binaries[item] = absolute_path
                else:
                    continue
        for name, path in binaries.items():
            print 'POST %s %s' % (base_url, str(dict(name=name, path=path)))
            requests.post(base_url, json.dumps(dict(name=name, path=path)))

    def is_valid(self, filename, args):
        checkers = {
            'startswith': lambda name, part: name.startswith(part),
            'endswith': lambda name, part: name.endswith(part),
            'has': lambda name, part: part in name,
        }
        for c in checkers.keys():
            if getattr(args, c) is not None:
                if not checkers[c](filename, getattr(args, c)):
                    return False
        # if we have passed all checks ensure it is a deb/rpm
        if not filename.endswith(('rpm', 'deb')):
            return False
        return True
