import hmac
from zope.component import getUtility
from zope.interface import implements
from AccessControl import getSecurityManager
from zExceptions import Forbidden
from ZPublisher.HTTPRequest import HTTPRequest
from Products.Five import BrowserView
from plone.keyring.interfaces import IKeyManager
from plone.protect.interfaces import IAuthenticatorView
from urlparse import urlparse

try:
    from hashlib import sha1 as sha
except ImportError:
    import sha


def _getUserName():
    user = getSecurityManager().getUser()
    if user is None:
        return "Anonymous User"
    return user.getUserName()


def _parseHost(url):
    parse = urlparse(url)
    return getattr(parse, 'netloc', parse[1])


def _verify(request, extra='', name='_authenticator'):
    referer = request.environ.get('HTTP_REFERER')
    if referer:
        if _parseHost(referer) != _parseHost(request.URL):
            return False

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
