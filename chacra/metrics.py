"""
A wrapper around python-statsd to automatically configure outgoing metrics so
that it can include, at the highest level::

    secret.hostname.module

Production Graphite instances might require a secret key which should be
prefixed to outgoing metrics, if not configured, metrics would start off from
the short hostname::

    hostname.module

Instantiating metrics work similarly to creating a logger instance::

    from metrics import Counter

    counter = Counter(__name__)

    counter += 1

It is allowed to alter the naming appending a suffix::


    def my_oddly_named_function():
        counter = Counter(__name__, suffix='expensive_function')
        while True:
            ...
            counter +=1

This would append 'package.module' with `expensive_function`, but
just the suffix (the last part of the scheme). For a production host, this
counter could look like::

    secret.chacra1.chacra.asynch.expensive_function


Although not encouraged, it is possible to fully override with a custom name::


    counter = Counter('custom.path')

Which would cause to override the module path (secret key and hostname would
prevail)::

    secret.chacra1.custom.path


..note:: All these assume a local statsd instance running, so there is no need
to provide a connection object. If there is ever a need to customize the
connection, it will need to be provided here.

"""

import socket
import pecan
import statsd


def short_hostname(_socket=None):
    """
    Returns the config option ``short_hostname`` if found.

    If ``short_hostname`` is not defined, it obtains the
    remote hostname of the socket and cuts off the domain part
    of its FQDN.
    """
    short_hostname = getattr(pecan.conf, 'short_hostname', None)
    if not short_hostname:
        _socket = _socket or socket
        return _socket.gethostname().split('.', 1)[0]
    return short_hostname


def get_prefix(conf=None, host=None):
    host = host or short_hostname()
    conf = conf or pecan.conf
    secret = getattr(conf, 'graphite_api_key', None)

    if secret:
        prefix = "%s.%s" % (secret, host)
    else:
        prefix = "%s" % host

    return prefix


def append_suffix(name, suffix):
    """
    Helper to append a suffix the end of the name with a custom one. Useful for
    private functions or signatures that require distinct separation from the
    module.
    """
    name_parts = name.split('.')
    name_parts.append(suffix)
    return '.'.join(name_parts)


def Counter(name, suffix=None):
    if suffix:
        name = append_suffix(name, suffix)
    return statsd.Counter("%s.%s" % (get_prefix(), name))


def Gauge(name, suffix=None):
    if suffix:
        name = append_suffix(name, suffix)
    return statsd.Gauge("%s.%s" % (get_prefix(), name))


def Timer(name, suffix=None):
    if suffix:
        name = append_suffix(name, suffix)
    return statsd.Timer("%s.%s" % (get_prefix(), name))
