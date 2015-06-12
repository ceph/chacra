chacra
======
A REST API for storing and retrieving specific versions and arquitectures of
(binary) packages.


The URL structure is very simple and allows to be explicit about what the type
and version of a given binary package the API is providing::

    /projects/{package_name}/{version}/{distribution}/{distro_release}/{architecture}/$binary

So for a CentOS 7 x86_64 package for Ceph the url could look like::

    /projects/ceph/firefly/centos/7/x86_64/ceph-0.87.2-0.el7.centos.x86_64.rpm


Self-discovery
--------------
The API provides informational JSON at every step of the URL about what is
available as a resource. The following examples show informational output that
can be consumed to dig deeper into the URL structure:

``GET /projects/``::

    {
        "ceph": {
            "name": "ceph",
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        },
        "ceph-deploy": {
            "name": "ceph-deploy",
            "last_updated": "15 hours, 42 minutes, 28 seconds ago"
        }
    }


``GET /projects/ceph/``::

    {
        "firefly": {
            "name": "firefly",
            "distros": ["centos", "redhat", "debian", "ubuntu"],
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        },
    }


``GET /projects/ceph/firefly/``::

    {
        "centos": {
            "name": "centos",
            "versions": ["7", "6"],
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        },
        "redhat": {
            "name": "redhat",
            "versions": [],
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        },
        "debian": {
            "name": "debian",
            "versions": [],
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        },
        "ubuntu": {
            "name": "ubuntu",
            "versions": [],
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        }
    }

``GET /projects/ceph/firefly/centos/``::

    {
        "7": {
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        },
        "6": {
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        }
    }

``GET /projects/ceph/centos/7/``::

    {
        "x86_64": {
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        }
    }

``GET /projects/ceph/centos/7/x86_64/``::

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
There are two ways for querying for binary metadata captured by the system.

**specific querying**:
If the location for the binary is known then, following our example URL the
binary should be queried with a ``GET`` at::

    /projects/ceph/centos/10/x86_64?name=ceph-0.87.2-0.el10.centos.x86_64.rpm


HTTP Responses:

* *200*: Success.
* *400*: Invalid request. Body::

    { "msg": "invalid query params: {keys}" }


* *404*: Resource not found. When the parent URL doesn't exist and therefore
  cannot be queried. This would also indicate that the binary doesn't exist.

**search**:
If the location of a binary is not known, a search can be performed at::

    /search?name=ceph

Search terms don't need to be unique and successful responses will return an
array of items found along with metadata about locations::


HTTP Responses:

* *200*: Success. Body::

  [
    {
      "ceph-0.87.2-0.el10.centos.x86_64.rpm": {
          "url": "/projects/ceph/centos/10/x86_64/ceph-0.87.2-0.el10.centos.x86_64.rpm"
      }
    },
      "ceph-0.87.1-0.el10.centos.x86_64.rpm": {
          "url": "/projects/ceph/centos/10/x86_64/ceph-0.87.1-0.el10.centos.x86_64.rpm"
      },
    }
  ]




* *400*: Invalid request. Body::

    { "msg": "invalid query params: {keys}" }


Creating new resources
----------------------
``POST`` requests will create new resources when using the full url with all
the metadata parts including the filename *when uploading files*. For example::

    curl -F "image=@/home/user/repos/ceph-0.87.2-0.el10.centos.x86_64.rpm" chacra.ceph.com/projects/ceph/centos/10/x86_64/ceph-0.87.1-0.el10.centos.x86_64.rpm/

Note how a trailing slash is required as well as the full name of the binary.

If the binary exists **it will not get overwritten** unless the ``force`` value
is set. Otherwise a 400 is returned.

If the ``force`` flag is set and the binary is overwritten a 200 is returned.
If the resource does not exist, a 201 is returned.


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

For non-existing URLs a retroactive feature will create the rest of the url
structure. For example, a new distribution release for CentOS 10 that didn't
exist before at this url and for the following package::

    /projects/ceph/centos/10/x86_64/ceph-0.87.2-0.el10.centos.x86_64.rpm

Would create all the parts that didn't exist before ('10','x86_64', and
'ceph-0.87.2-0.el10.centos.x86_64.rpm' from our previous examples).

The body for the POST HTTP request would still require the "name" key::

    { "name": "ceph-0.87.2-0.el10.centos.x86_64.rpm" }

Optional (but recommended key) is the ``built-by``::


    {
        "name": "ceph-0.87.2-0.el10.centos.x86_64.rpm",
        "built-by": "alfredodeza"
    }


Force a rewrite of a binary
---------------------------
If a POST is done to a binary URL that already exists, the API will return
a 400 with a message indicating that the binary is already there.

But sometimes, rewriting a binary is needed and the API allows that with a flag
in the JSON object when doing a POST::

    {
        "name": "ceph-0.87.2-0.el10.centos.x86_64.rpm",
        "force": True
    }

HTTP Responses:

* *200*: Success.
* *400*: Invalid request. Body::

    { "msg": "resource already exists and 'force' flag was not set" }

