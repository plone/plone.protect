from decorator import decorator
from types import UnboundMethodType
from zope.globalrequest import getRequest


def protect(*checkers):
    @decorator
    def _protect(f, *args, **kw):
        request = getRequest()
        if request is not None:
            for checker in checkers:
                checker(request)
        return f(*args, **kw)

    def _method_func(f):
        if isinstance(f, UnboundMethodType):
            f = f.__func__
        return _protect(f)

    return _method_func
