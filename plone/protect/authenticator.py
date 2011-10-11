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


def _verify(request, extra=''):
    auth = request.get("_authenticator")
    if auth is None:
        return False

    manager = getUtility(IKeyManager)
    ring = manager[u"_system"]
    user = _getUserName()

    for key in ring:
        if key is None:
            continue
        correct = hmac.new(key, user + extra, sha).hexdigest()
        if correct == auth:
            return True

    return False


def createToken(extra=''):
    manager = getUtility(IKeyManager)
    secret = manager.secret()
    user = _getUserName()
    return hmac.new(secret, user + extra, sha).hexdigest()


class AuthenticatorView(BrowserView):
    implements(IAuthenticatorView)

    def authenticator(self, extra=''):
        auth = createToken(extra)
        return '<input type="hidden" name="_authenticator" value="%s"/>' % \
                auth

    def verify(self, extra=''):
        return _verify(self.request, extra)


def check(request, extra=''):
    if isinstance(request, HTTPRequest):
        if not _verify(request, extra=''):
            raise Forbidden('Form authenticator is invalid.')


def CustomCheckAuthenticator(extra=''):
    def _check(request):
        return check(request, extra)
    return _check


__all__ = ["AuthenticatorView", "check", "createToken",
           "CustomCheckAuthenticator"]
