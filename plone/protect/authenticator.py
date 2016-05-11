from AccessControl import getSecurityManager
from plone.keyring.interfaces import IKeyManager
from plone.protect.interfaces import IAuthenticatorView
from Products.Five import BrowserView
from zExceptions import Forbidden
from zope.component import getUtility
from zope.interface import implements
from ZPublisher.HTTPRequest import HTTPRequest

import hmac
try:
    from hashlib import sha1 as sha
except ImportError:
    import sha


ANONYMOUS_USER = "Anonymous User"


def isAnonymousUser(user):
    return user is None or user.getUserName() == ANONYMOUS_USER


def _getUserName():
    user = getSecurityManager().getUser()
    if user is None:
        return ANONYMOUS_USER
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


def _getKeyring(username, manager=None):
    if manager is None:
        manager = getUtility(IKeyManager)
    if username == ANONYMOUS_USER:
        try:
            ring = manager[u'_anon']
        except KeyError:
            # no anonymous key defined.
            # XXX should we even bother allowing to verify?
            ring = manager[u'_system']
    else:
        try:
            ring = manager[u"_forms"]
        except KeyError:
            ring = manager[u'_system']
    return ring


def _verify_request(request, extra='', name='_authenticator', manager=None):
    auth = request.get(name)
    if auth is None:
        auth = request.getHeader('X-CSRF-TOKEN')
        if auth is None:
            return False
    if isinstance(auth, list):
        # in case 2 auth attributes were added to form. It can happen
        auth = auth[0]

    user = _getUserName()
    ring = _getKeyring(user, manager=manager)

    for key in ring:
        if key is None:
            continue
        correct = hmac.new(key, user + extra, sha).hexdigest()
        if _is_equal(correct, auth):
            return True

    return False

# We had to rename because previous hotfixes patched _verify
_verify = _verify_request


def createToken(extra='', manager=None):
    user = _getUserName()
    ring = _getKeyring(user, manager=manager)
    secret = ring.random()
    return hmac.new(secret, user + extra, sha).hexdigest()


class AuthenticatorView(BrowserView):
    implements(IAuthenticatorView)

    def token(self, extra=''):
        return createToken(extra)

    def authenticator(self, extra='', name='_authenticator'):
        auth = createToken(extra)
        return '<input type="hidden" name="%s" value="%s"/>' % (name, auth)

    def verify(self, extra='', name="_authenticator"):
        return _verify_request(self.request, extra=extra, name=name)


def check(request, extra='', name="_authenticator", manager=None):
    if isinstance(request, HTTPRequest):
        if not _verify_request(request, extra=extra, name=name, manager=manager):
            raise Forbidden('Form authenticator is invalid.')


def CustomCheckAuthenticator(extra='', name='_authenticator'):
    def _check(request):
        return check(request, extra=extra, name=name)
    return _check


__all__ = ["AuthenticatorView", "check", "createToken",
           "CustomCheckAuthenticator"]
