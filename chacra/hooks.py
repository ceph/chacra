import logging
from pecan.hooks import PecanHook


log = logging.getLogger(__name__)


class CustomErrorHook(PecanHook):
    """
    Only needed for prod environments where it looks like multi-worker servers
    will swallow exceptions. This will ensure a traceback is logged correctly.
    """

    def on_error(self, state, exc):
        log.exception('unhandled error by Chacra')

