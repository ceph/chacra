chacra
======
A REST API for storing and retrieving specific versions and architectures of
(binary) packages.


The URL structure is very simple and allows to be explicit about what the type
and version of a given binary package the API is providing::

    /projects/{package_name}/{version}/{distribution}/{distro_release}/{architecture}/$binary

So for a CentOS 7 x86_64 package for Ceph the url could look like::

    /projects/ceph/firefly/centos/7/x86_64/ceph-0.87.2-0.el7.centos.x86_64.rpm


Configuration
-------------
The service needs to be configured with a few items to correctly work with
binaries.

binary_root
^^^^^^^^^^^
The ``binary_root`` is a required configuration item, it defines where binaries
live so that when a new binary is POSTed the service will use this path to save
the binary to.

credentials
^^^^^^^^^^^
The POST and DELETE HTTP methods are protected by default using basic HTTP
authentication. The credentials must be defined in the configuration file for
the service as follows::

    api_user = 'username'
    api_key = 'secret'



Self-discovery
--------------
The API provides informational JSON at every step of the URL about what is
available as a resource. The following examples show informational output that
can be consumed to dig deeper into the URL structure:

``GET /projects/``::

    {
        "ceph": ["firefly", "giant", "hammer"],
        "ceph-deploy": ["master"]
    }


``GET /projects/ceph/``::

    {
        "firefly": ["centos", "redhat", "debian", "ubuntu"]
    }


``GET /projects/ceph/firefly/``::

    {
        "centos": ["7", "6"],
        "debian": ["wheezy"],
        "ubuntu": ["trusty"],
    }

``GET /projects/ceph/firefly/centos/``::

    {
        "7": ["x86_64"],
        "6": ["x86_64"]
    }

``GET /projects/ceph/firefly/centos/7/``::

    {
        "x86_64": ["ceph-0.87.2-0.el7.centos.x86_64.rpm"]
    }

``GET /projects/ceph/firefly/centos/7/x86_64/``::

    {
        "ceph-0.87.2-0.el7.centos.x86_64.rpm": {
            "signed": True,
            "size": "12M",
            "last_updated": "14 hours, 39 minutes, 19 seconds ago",
            "built-by": "ktdreyer",
        },
        "ceph-0.87.1-0.el7.centos.x86_64.rpm": {
            "signed": True,
            "size": "12M",
            "last_updated": "20 days, 6 hours, 39 minutes, 19 seconds ago",
            "built-by": "ktdreyer",
        },
        "ceph-0.87-0.el7.centos.x86_64.rpm": {
            "signed": True,
            "size": "12M",
            "last_updated": "35 days, 6 hours, 39 minutes, 19 seconds ago",
            "built-by": "alfredodeza",
        }

    }

At this point, the keys for the JSON object represent the available binaries
for the next part of the URL.

So another ``GET`` operation on that final URL would retrieve the actual
binary. Other metadata may be provided, but the rule would be that all
top-level keys are meant to be part of the consumable url.


Querying binary information
---------------------------
The search endpoint is ``/search/`` and accepts a few keyword arguments. At the
moment only simple querying is allowed (only matches are used) and no other
logical operators can be used, like ``>=`` for example.

In its most simple form a query would look like::

    /search/?name=ceph

Search terms don't need to be unique and successful responses will return an
array of items found along with metadata about locations.

The supported query parameters are:

* ``distro``
* ``distro_version``
* ``arch``
* ``ref``
* ``built_by``
* ``size``
* ``name``


HTTP Responses:

* *200*: Success. Body::

    [
      {
        "ceph-0.87.2-0.el10.centos.x86_64.rpm": {
            "url": "/projects/ceph/firefly/centos/10/x86_64/ceph-0.87.2-0.el10.centos.x86_64.rpm"
        }
      },
        "ceph-0.87.1-0.el10.centos.x86_64.rpm": {
            "url": "/projects/ceph/firefly/centos/10/x86_64/ceph-0.87.1-0.el10.centos.x86_64.rpm"
        },
      }
    ]



HTTP Responses:

* *200*: Success.
* *400*: Invalid request. Body::

    { "msg": "invalid query params: {keys}" }



File resources
--------------
``POST`` requests will create new resources when using the full url with all
the metadata parts including the filename *when uploading files*. For example::

    curl -F "file=@/home/user/repos/ceph-0.87.2-0.el10.centos.x86_64.rpm" chacra.ceph.com/projects/ceph/firefly/centos/10/x86_64/ceph-0.87.1-0.el10.centos.x86_64.rpm/

Note how a trailing slash is required as well as the full name of the binary.

If the binary exists **it will not get overwritten** unless the ``force`` value
is set. Otherwise a 400 is returned.

If the ``force`` flag is set and the binary is overwritten a 200 is returned.
If the resource does not exist, a 201 is returned.

File uploads **cannot** create metadata other than the file path where the
binary is stored at.

User must configure the location of binary uploads in the config file, for
a location relative to where the config file lives::

    binary_root = '%(confdir)s/public'

Or any other absolute path is allowed too::

    binary_root = '/opt/binaries'


Directory paths will follow the same structure as in URLs. For example, with
a ``binary_root`` key that points to ``/opt/binaries/`` the final location for
a resource that lives in
``/projects/ceph/firefly/centos/10/x86_64/ceph-0.87.1-0.el10.centos.x86_64.rpm/`` would
be
``/opt/binaries/ceph/firefly/centos/10/x86_64/ceph-0.87.1-0.el10.centos.x86_64.rpm/``

HTTP Responses:

* *200*: Resource was updated
* *201*: Resource was created
* *400*: Invalid request. Body::

    { "msg": "resource already exists and 'force' flag was not set" }


``POST`` will create new items at given parts of the URL. For example, to
create a new package, a ``POST`` to ``/projects/`` with an HTTP body that
should look like::

    { "name": "my_new_package" }

For other parts of the URL the ``"name"`` key is also required.

HTTP Responses:

* *200*: Success.
* *400*: Invalid request. Body::

    { "msg": "my_new_package already exists" }


Binary metadata updates
-----------------------
For non-existing URLs a retroactive feature will create the rest of the url
structure. For example, a new distribution release for CentOS 10 that didn't
exist before at this url and for the following package::

    /projects/ceph/firefly/centos/10/x86_64/ceph-0.87.2-0.el10.centos.x86_64.rpm

Would create all the parts that didn't exist before ('10','x86_64', and
'ceph-0.87.2-0.el10.centos.x86_64.rpm' from our previous examples). This would
happen with file uploads too.

The body for the POST HTTP request would still require the "name" key::

    { "name": "ceph-0.87.2-0.el10.centos.x86_64.rpm" }

Optional (but recommended key) is the ``built-by``::


    {
        "name": "ceph-0.87.2-0.el10.centos.x86_64.rpm",
        "built-by": "alfredodeza"
    }

These requests need to go to the parent url part, so for the example above the
HTTP request would go to::

    /projects/ceph/firefly/centos/10/x86_64/

Note the need for a trailing slash.


Force a rewrite of a binary metadata
------------------------------------
If a POST is done to a binary URL that already exists, the API will return
a 400 with a message indicating that the binary is already there.

But sometimes, rewriting a binary is needed and the API allows that with a flag
in the JSON object when doing a POST::

    {
        "name": "ceph-0.87.2-0.el10.centos.x86_64.rpm",
        "force": True
    }

Again, note that this ``POST`` would need to go to the root of the url, following
the examples above that would mean::


    /projects/ceph/firefly/centos/10/x86_64/

Note the need for a trailing slash.


HTTP Responses:

* *200*: Success.
* *400*: Invalid request. Body::

    { "msg": "resource already exists and 'force' flag was not set" }


Automatic Repositories
======================
This service provides automatic repository creation per distribution version,
with optional handling of *combined* repositories in the case of DEB packages.

The default repository structure URL looks like::

    /repos/{project}/{ref}/{distro}/{distro version}/{REPO}

For the Ceph project, the production URL repository structure for RPMs looks
like::

    /repos/{project}/rpm-{ref}/{distro}{distro version}/{REPO}

And for DEB packages is::

    /repos/{project}/debian-{ref}/{combined REPO}

``{combined REPO}`` is the case where in a DEB repository, packages for
multiple distribution versions can exist in the same repository.

DEBIAN
------
To alter default structure with a custom name, like in production repos
the configuration needs to be updated per project. Repos can only be created *per*
REF, although configuration is done at PROJECT level, affecting all REFs. For example
in config.py::

    repos = {
        'ceph': {
            'deb': {
              'combined': True,
              'versions': ['wheezy', 'precise', 'jessie']
            },
            # 'rpm' is not defined as there is currently no immediate need to design a custom
            # structure, so it is left undefined on purpose.
        }
    }

The above configuration would cause "combined" repositories of the defined
versions. The repository would then be available at::

    /repos/{project}/{ref}/debian/{combined REPO}

If the `combined` key was undefined or explicitly set to `False` then the
repositories would follow the default structure:

    /repos/{project}/{ref}/debian/{distro version}/{REPO}


For extra packages that may be coming from other projects, the configuration structure will allow
for definition of them. For example, 'ceph-deploy' exists publicly in the 'ceph' repositories, just
like 'radosgw-agent'. This inclusion would be defined at the project level, like::

    repos = {
        'ceph': {
            'extras': ['ceph-deploy', 'radosgw-agent'],
            'deb': {
              'combined': True,
              'versions': ['wheezy', 'precise', 'jessie']
            },
        }
    }

The `extras` key would require those projects to be present in the chacra
instance that is creating the repositories.
# TODO: Maybe allow for URLs as well? That way packages could come from another source?

RPM
---
Default repo structure for Firefly Ceph on CentOS 7 would look like::

    /repos/ceph/firefly/centos/7/{REPO}

This default structure would be good enough to be promoted to production,
because the parent directory structure would not matter at this point as it is
only the {REPO} that can have any destination (vs. DEBs which are intertwined
within the repository). This is the reason why there is no need to define
a configuration strategy for RPM repositories.

about the name
==============
`chakra` is a quechua word to refer to a small farm in the outskirts, dedicated
to produce food for the city.

Reference: https://en.wikipedia.org/wiki/Quechua
