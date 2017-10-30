import logging
from webob.exc import WSGIHTTPException
from pecan.hooks import PecanHook


log = logging.getLogger(__name__)


class CustomErrorHook(PecanHook):
    """
    Only needed for prod environments where it looks like multi-worker servers
    will swallow exceptions. This will ensure a traceback is logged correctly.
    """

    def on_error(self, state, exc):
        if isinstance(exc, WSGIHTTPException):
            if exc.code == 404:
                log.error("Not Found: %s" % state.request.url)
                return
            # explicit redirect codes that should not be handled at all by this
            # utility
            elif exc.code in [300, 301, 302, 303, 304, 305, 306, 307, 308]:
                return

        log.exception('unhandled error by Chacra')

