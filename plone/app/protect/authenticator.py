import inspect
import hmac
import sha
from zope.component import getUtility
from zope.interface import implements
from AccessControl import getSecurityManager
from AccessControl.requestmethod import _buildFacade
from zExceptions import Forbidden
from ZPublisher.HTTPRequest import HTTPRequest
from Products.Five import BrowserView
from plone.keyring.interfaces import IKeyManager
from plone.app.protect.interfaces import IAuthenticatorView

def _getUserName():
    user=getSecurityManager().getUser()
    if user is None:
        return "Anonymous User"
    return user.getUserName()


def _verify(request):
        auth=request.get("_authenticator")
        if auth is None:
            return False

        manager=getUtility(IKeyManager)
        ring=manager[u"_system"]
        user=_getUserName()

        for key in ring:
            if key is None:
                continue
            correct=hmac.new(key, user, sha).hexdigest()
            if correct==auth:
                return True

        return False

class AuthenticatorView(BrowserView):
    implements(IAuthenticatorView)

    def authenticator(self):
        manager=getUtility(IKeyManager)
        secret=manager.secret()
        user=_getUserName()
        auth=hmac.new(secret, user, sha).hexdigest()
        return '<input type="hidden" name="_authenticator" value="%s"/>' % \
                auth


    def verify(self):
        return _verify(self.request)


_default = []

# This is based on AccessControl.requestmethod.postonly
def AuthenticateForm(callable):
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
        if isinstance(request, HTTPRequest):
            if not _verify(request):
                raise Forbidden('Form authenticator is invalid.')

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
    exec _buildFacade(spec, callable.__doc__) in facade_globs
    return facade_globs['_facade']


__all__ = [ "AuthenticatorView", "AuthenticateForm" ]

