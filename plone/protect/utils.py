from AccessControl.requestmethod import _buildFacade
from plone.protect.authenticator import createToken
from zope.globalrequest import getRequest

import inspect

_default = []

# This is based on AccessControl.requestmethod.postonly
# It should probably be updated to use the decorator module.


class protect(object):

    def __init__(self, *checkers):
        self.checkers = checkers

    def __call__(self, callable):
        spec = inspect.getargspec(callable)
        args, defaults = spec[0], spec[3]
        try:
            r_index = args.index("REQUEST")
        except ValueError:
            raise ValueError("No REQUEST parameter in callable signature")

        arglen = len(args)
        if defaults is not None:
            defaults = zip(args[arglen - len(defaults):], defaults)
            arglen -= len(defaults)

        def _curried(*args, **kw):
            request = None

            if len(args) > r_index:
                request = args[r_index]

            for checker in self.checkers:
                checker(request)

            # Reconstruct keyword arguments
            if defaults is not None:
                args, kwparams = args[:arglen], args[arglen:]
                for positional, (key, default) in zip(kwparams, defaults):
                    if positional is _default:
                        kw[key] = default
                    else:
                        kw[key] = positional

            return callable(*args, **kw)

        # Build a facade, with a reference to our locally-scoped _curried
        facade_globs = dict(_curried=_curried, _default=_default)
        try:
            name = callable.__name__
            exec _buildFacade(name, spec, callable.__doc__) in facade_globs
        except TypeError:  # BBB: Zope 2.10
            name = '_facade'
            exec _buildFacade(spec, callable.__doc__) in facade_globs
        return facade_globs[name]


def addTokenToUrl(url, req=None):
    if not url:
        return url
    if req is None:
        req = getRequest()
    if not url.startswith(req.SERVER_URL):
        # only transforms urls to same site
        return url
    if '_auth_token' not in req.environ:
        # let's cache this value since this could be called
        # many times for one request
        req.environ['_auth_token'] = createToken()
    token = req.environ['_auth_token']

    if '_authenticator' not in url:
        if '?' not in url:
            url += '?'
        else:
            url += '&'
        url += '_authenticator=' + token
    return url
