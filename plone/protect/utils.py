from decorator import decorator
from zope.globalrequest import getRequest


def protect(*checkers):
    @decorator
    def _protect(f, *args, **kw):
        request = getRequest()
        if request is not None:
            for checker in checkers:
                checker(request)
        return f(*args, **kw)
    return _protect
