# import StringIO for Python 2 or 3
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from contextlib import contextmanager

class CapturedText(object):
    log_path = None

@contextmanager
def captured(name=None, log_path = None):
    """
    Context manager to capture the printed output of the code in the with block

    Bind the context manager to a variable using `as` and the result will be
    in the stdout property.

    >>> from tests.helpers import capture
    >>> with captured() as c:
    ...     print('hello world!')
    ...
    >>> c.stdout
    'hello world!\n'
    """
    import sys

    stdout = sys.stdout
    stderr = sys.stderr


    if log_path:
        sys.stdout = sys.stderr = open(log_path, "w", 1)
    else:
        sys.stdout = sys.stderr = StringIO()
    c = CapturedText()
    c.name = name
    c.outfile = sys.stdout
    c.log_path = log_path

    yield c

    if log_path:
        c.outfile.close()

    sys.stdout = stdout
    sys.stderr = stderr