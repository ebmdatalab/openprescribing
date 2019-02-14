import logging
import sys
import traceback

logger = logging.getLogger(__name__)


class BatchedEmailErrors(Exception):
    def __init__(self, exceptions):
        individual_messages = set()
        for exception in exceptions:
            individual_messages.add(
                "".join(traceback.format_exception_only(
                    exception[0], exception[1])).strip())
        if len(exceptions) > 1:
            msg = ("Encountered %s mail exceptions "
                   "(showing last traceback only): `%s`" % (
                       len(exceptions),
                       ", ".join(individual_messages)))
        else:
            msg = individual_messages.pop()
        super(BatchedEmailErrors, self).__init__(msg)


class EmailErrorDeferrer(object):
    """Defers raising an exception until `max_errors` is reached,
    whereupon a new summary exception is raised.

    """
    def __init__(self, max_errors=3):
        self.exceptions = []
        self.max_errors = max_errors

    def try_email(self, callback, *args):
        try:
            callback(*args)
        except Exception as e:
            self.exceptions.append(sys.exc_info())
            logger.exception(e)
            if len(self.exceptions) > self.max_errors:
                raise (BatchedEmailErrors(self.exceptions),
                       None, self.exceptions[-1][2])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.exceptions:
            exception = BatchedEmailErrors(self.exceptions)
            raise (exception,
                   None,
                   self.exceptions[-1][2])
