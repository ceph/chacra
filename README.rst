chacra
======
A REST API for storing and retrieving specific versions and architectures of
(binary) packages.


The URL structure is very simple and allows to be explicit about what the type
and version of a given binary package the API is providing::

    /binaries/{package_name}/{version}/{sha1}/{distribution}/{distro_release}/{architecture}/$binary

So for a CentOS 7 x86_64 package for Ceph the url could look like::

    /binaries/ceph/firefly/87a7cec9ab11c677de2ab23a7668a77d2f5b955e/centos/7/x86_64/ceph-0.87.2-0.el7.centos.x86_64.rpm


Configuration
-------------
The service needs to be configured with a few items to correctly work with
binaries.

binary_root
^^^^^^^^^^^
The ``binary_root`` is a required configuration item, it defines where binaries
live so that when a new binary is POSTed the service will use this path to save
the binary to.

distributions_root
^^^^^^^^^^^^^^^^^^

The ``distributions_root`` is a required configuration item, it defines where the
project specific distributions files will be stored when creating debian repositories.

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

``GET /binaries/``::

    {
        "ceph": ["firefly", "giant", "hammer"],
        "ceph-deploy": ["master"]
    }


``GET /binaries/ceph/``::

    {
        "firefly": ["centos", "redhat", "debian", "ubuntu"]
    }


``GET /binaries/ceph/firefly/``::

    {
        "head": ["centos", "debian", "ubuntu"],
        "95c4287b5d24b762bc8538633c5bb2918ecfe4dd": ["centos"],
    }

``GET /binaries/ceph/firefly/head/``::

    {
        "centos": ["7", "6"],
        "debian": ["wheezy"],
        "ubuntu": ["trusty"],
    }

``GET /binaries/ceph/firefly/head/centos/``::

    {
        "7": ["x86_64"],
        "6": ["x86_64"]
    }

``GET /binaries/ceph/firefly/head/centos/7/``::

    {
        "x86_64": ["ceph-0.87.2-0.el7.centos.x86_64.rpm"]
    }

``GET /binaries/ceph/firefly/head/centos/7/x86_64/``::

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

    /search/?name=ceph_10.0.0_el6.x86_64.rpm

Successful responses will return an array of items found along with metadata
about locations.

The supported query parameters are:

* ``distro``
* ``distro_version``
* ``arch``
* ``ref``
* ``built_by``
* ``size``
* ``name``

These require to have exact matches. For example a query like
``?distro=CentOS`` would not return binaries that have a ``centos`` distro
value.

Search terms that allow more flexiblity are:

* ``name-has``

The ``-has`` connotation means that any part of the binary name (in this case)
can have that value. For example a query like ``?name-has=deploy`` would match
a binary like ``ceph-deploy_1.5.21_all.deb``.


HTTP Responses:

* *200*: Success. Body::

    [
      {
        "ceph-0.87.2-0.el10.centos.x86_64.rpm": {
            "url": "/binaries/ceph/firefly/centos/10/x86_64/ceph-0.87.2-0.el10.centos.x86_64.rpm"
        }
      },
        "ceph-0.87.1-0.el10.centos.x86_64.rpm": {
            "url": "/binaries/ceph/firefly/centos/10/x86_64/ceph-0.87.1-0.el10.centos.x86_64.rpm"
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

    curl -F "file=@/home/user/repos/ceph-0.87.2-0.el10.centos.x86_64.rpm" https://chacra.ceph.com/binaries/ceph/firefly/head/centos/10/x86_64/

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
``/binaries/ceph/firefly/head/centos/10/x86_64/ceph-0.87.1-0.el10.centos.x86_64.rpm/`` would
be
``/opt/binaries/ceph/firefly/head/centos/10/x86_64/ceph-0.87.1-0.el10.centos.x86_64.rpm/``

HTTP Responses:

* *200*: Resource was updated
* *201*: Resource was created
* *400*: Invalid request. Body::

    { "msg": "resource already exists and 'force' flag was not set" }


``POST`` will create new items at given parts of the URL. For example, to
create a new package, a ``POST`` to ``/binaries/`` with an HTTP body that
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

    /binaries/ceph/firefly/head/centos/10/x86_64/ceph-0.87.2-0.el10.centos.x86_64.rpm

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

    /binaries/ceph/firefly/head/centos/10/x86_64/

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


    /binaries/ceph/firefly/centos/10/x86_64/

Note the need for a trailing slash.


HTTP Responses:

* *200*: Success.
* *400*: Invalid request. Body::

    { "msg": "resource already exists and 'force' flag was not set" }


Automatic Repositories
======================
This service provides automatic repository creation per distribution version
(enabled by default), with optional handling of *combined* repositories in the
case of DEB packages.

The default repository structure URL looks like::

    /repos/{project}/{ref}/{sha1}/{distro}/{distro version}/{REPO}

The type of repository (rpm or deb) is usually inferred from the type
of binaries uploaded; however, 'raw' repos are also supported.  To set
the repo type, POST to the repo URL and include a data payload that contains
a JSON structure

    {"type": "raw"}


Defining custom repositories
----------------------------
To create repos that combine multiple distro versions, define them in ``repos``
dictionary in your config. Repos can only be created *per* REF, although
configuration is done at PROJECT level, affecting all REFs. For example
in config.py::

    repos = {
        'ceph': {
            'combined': ['wheezy', 'precise', 'jessie'],
        }
    }

The above configuration would create a "combined" repository of the defined
versions. The repository would then be available at::

    /repos/{project}/{ref}/{sha1}/combined/{combined REPO}

All other repos built for other other distro versions will still be available at the
default endpoint::

    /repos/{project}/{ref}/{sha1}/{distro}/{distro version}/{REPO}


.. note::

    Creating a repository that combines multiple distro versions is only available for
    debian based distros.


Defining extra packages
-----------------------

For extra packages that may be coming from other projects, the configuration structure will allow
for definition of them. For example, 'ceph-deploy' exists publicly in the 'ceph' repositories, just
like 'radosgw-agent'. This inclusion would be defined at the project level, like::


    repos = {
        'ceph': {
            'all': {
                'ceph-deploy': ['all'],
            },
            'firefly' {
                'radosgw-agent': ['all'],
                'ceph-deploy': ['v1.0.0', 'v1.1.1'],
            },
            'hammer' {
                'radosgw-agent': ['all'],
            },
            'giant' {
                'radosgw-agent': ['all'],
            },
            'combined': ['wheezy', 'precise', 'jessie'],
        }
    }



The `extras` key would require those projects to be present in the chacra
instance that is creating the repositories.
# TODO: Maybe allow for URLs as well? That way packages could come from another source?


Disabling repositories
----------------------
Repository creation can be disabled (on by default) in the configuration for
repos. In the case of a project like ``ceph-deploy`` that is usually included
in other repos, it could be disabled like::

    repos = {
        'ceph-deploy': {
            'disabled': True
        }
    }

And it can also be disabled if a repository is not configured with::

    disable_unconfigured_repos = True

A repository is considered as *unconfigured* if it doesn't have an entry in the
``repos`` dictionary.


Disabling Automatic Repositories
--------------------------------
This is a special kind of behavior where a new binary uploaded will trigger
a repository to be created (or updated). If a project is of interest to other
projects (e.g. project1 binaries should be included in project2) this can
trigger unwanted behavior.

Or if a build process is uploading several binaries at the same time, it might
be desirable to wait for repo creation until the very end.

To disable this automatic behavior, and similar to disabling repositories, the
configuration can be done per project::

    repos = {
        'ceph-deploy': {
            'automatic': False
        }
    }

Configuring distributions
-------------------------
Creating a debian repository requires a distributions file be created. Chacra will create these for each project
by using the following configuration::

    distributions = {
       "defaults": {
            "DebIndices": "Packages Release . .gz .bz2",
            "DscIndices": "Sources Release .gz .bz2",
            "Contents": ".gz .bz2",
            "Origin": "ceph.com",
            "Description": "",
            "Architectures": "amd64 armhf i386 source",
            "Suite": "stable",
            "Components": "main",
            "DDebComponents": "main",
        },
        "ceph": {
            "Description": "Ceph distributed file system",
        },
    }

The ``defaults`` key is used for any project that doesn't have it's own explicitly defined key. This key isn't required,
but it can be usueful when you have many projects with similar values in their distributions files.

If you want to add keys or modify keys that exist in ``defaults`` for a specific project, add that project name as
a key of ``distributions`` and define the keys you'd need to override or add there.

Authentication
==============

If authentication is configured, you can use the following flags to curl:

curl --basic -u myuser -k -F "file=@ceph-deploy-1.5.28-0.noarch.rpm" https://chacra.example.com/binaries/ceph/test/head/centos/10/x86_64/

You should also investigate https://pypi.python.org/pypi/chacractl, a client
that wraps the chacra API and handles authentication in a configuration file,
etc.

about the name
==============
`chakra` is a quechua word to refer to a small farm in the outskirts, dedicated
to produce food for the city.

Reference: https://en.wikipedia.org/wiki/Quechua
