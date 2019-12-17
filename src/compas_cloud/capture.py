# import StringIO for Python 2 or 3
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from contextlib import contextmanager

class CapturedText(object):
    pass

@contextmanager
def captured(name=None):
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

    sys.stdout = outfile = StringIO()
    sys.stderr = errfile = StringIO()
    c = CapturedText()
    c.name = name
    c.outfile = outfile
    c.errfile = errfile
    c.finished = False
    yield c
    # c.stdout = outfile.getvalue()
    # c.stderr = errfile.getvalue()

    sys.stdout = stdout
    sys.stderr = stderr