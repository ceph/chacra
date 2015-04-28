chacra
======
A REST API for storing and retrieving specific versions and arquitectures of
(binary) packages.


The URL structure is very simple and allows to be explicit about what the type
and version of a given binary package the API is providing::

    /packages/{package_name}/{distribution}/{distro_release}/{architecture}/$binary

### FIXME REVISIT THIS::
    /packages/{package_name}/distributions/{distribution}/releases/{distro_release}/archs/{architecture}/$binary

So for a CentOS 7 x86_64 package for Ceph the url could look like::

    /packages/ceph/centos/7/x86_64/ceph-0.87.2-0.el7.centos.x86_64.rpm


Self-discovery
--------------
The API provides informational JSON at every step of the URL about what is
available as a resource. The following examples show informational output that
can be consumed to dig deeper into the URL structure:

``GET /packages/``::

    {
        "ceph": {
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        },
        "ceph-deploy": {
            "last_updated": "15 hours, 42 minutes, 28 seconds ago"
        },
        "radosgw-agent": {
            "last_updated": "12 hours, 56 minutes, 8 seconds ago"
        }

    }

``GET /packages/ceph/``::

    {
        "centos": {
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        },
        "redhat": {
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        },
        "debian": {
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        },
        "ubuntu": {
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        }
    }

``GET /packages/ceph/centos/``::

    {
        "7": {
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        },
        "6": {
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        }
    }

``GET /packages/ceph/centos/7/``::

    {
        "x86_64": {
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        }
    }

``GET /packages/ceph/centos/7/x86_64/``::

    {
        "ceph-0.87.2-0.el7.centos.x86_64.rpm": {
            "signed": True,
            "size": "12M"
            "last_updated": "14 hours, 39 minutes, 19 seconds ago"
        },
        "ceph-0.87.1-0.el7.centos.x86_64.rpm": {
            "signed": True,
            "size": "12M"
            "last_updated": "20 days, 6 hours, 39 minutes, 19 seconds ago"
        },
        "ceph-0.87-0.el7.centos.x86_64.rpm": {
            "signed": True,
            "size": "12M"
            "last_updated": "35 days, 6 hours, 39 minutes, 19 seconds ago"
        }

    }

At this point, the keys for the JSON object represent the available binaries
for the next part of the URL.

So another ``GET`` operation on that final URL would retrieve the actual
binary. Other metadata may be provided, but the rule would be that all
top-level keys are meant to be part of the consumable url.


Creating new items
------------------
``POST`` will create new items at given parts of the URL. For example, to
create a new package, a ``POST`` to ``/packages/`` with an HTTP body that
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

    /packages/ceph/centos/10/x86_64/ceph-0.87.2-0.el10.centos.x86_64.rpm

Would create all the parts that didn't exist before ('10','x86_64', and
'ceph-0.87.2-0.el10.centos.x86_64.rpm' from our previous examples).

The body for the POST HTTP request would still require the "name" key::

    { "name": "ceph-0.87.2-0.el10.centos.x86_64.rpm" }


