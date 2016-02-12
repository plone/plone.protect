import hmac
from zope.component import getUtility
from zope.interface import implements
from AccessControl import getSecurityManager
from zExceptions import Forbidden
from ZPublisher.HTTPRequest import HTTPRequest
from Products.Five import BrowserView
from plone.keyring.interfaces import IKeyManager
from plone.protect.interfaces import IAuthenticatorView

try:
    from hashlib import sha1 as sha
except ImportError:
    import sha


def _getUserName():
    user = getSecurityManager().getUser()
    if user is None:
        return "Anonymous User"
    return user.getUserName()


def _is_equal(val1, val2):
    """
    constant time comparison
    """
    if not isinstance(val1, basestring) or not isinstance(val2, basestring):
        return False
    if len(val1) != len(val2):
        return False
    result = 0
    for x, y in zip(val1, val2):
        result |= ord(x) ^ ord(y)
    return result == 0


def _verify(request, extra='', name='_authenticator'):
    auth = request.get(name)
    if auth is None:
        return False

    manager = getUtility(IKeyManager)
    ring = manager[u"_system"]
    user = _getUserName()

    for key in ring:
        if key is None:
            continue
        correct = hmac.new(key, user + extra, sha).hexdigest()
        if _is_equal(correct, auth):
            return True

    return False


def createToken(extra=''):
    manager = getUtility(IKeyManager)
    secret = manager.secret()
    user = _getUserName()
    return hmac.new(secret, user + extra, sha).hexdigest()


class AuthenticatorView(BrowserView):
    implements(IAuthenticatorView)

    def token(self, extra=''):
        return createToken(extra)

    def authenticator(self, extra='', name='_authenticator'):
        auth = createToken(extra)
        return '<input type="hidden" name="%s" value="%s"/>' % (
                name, auth)

    def verify(self, extra='', name="_authenticator"):
        return _verify(self.request, extra=extra, name=name)


def check(request, extra='', name="_authenticator"):
    if isinstance(request, HTTPRequest):
        if not _verify(request, extra=extra, name=name):
            raise Forbidden('Form authenticator is invalid.')


def CustomCheckAuthenticator(extra='', name='_authenticator'):
    def _check(request):
        return check(request, extra=extra, name=name)
    return _check


__all__ = ["AuthenticatorView", "check", "createToken",
           "CustomCheckAuthenticator"]
