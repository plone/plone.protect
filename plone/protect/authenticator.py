import hmac
import sha
from zope.component import getUtility
from zope.interface import implements
from AccessControl import getSecurityManager
from zExceptions import Forbidden
from ZPublisher.HTTPRequest import HTTPRequest
from Products.Five import BrowserView
from plone.keyring.interfaces import IKeyManager
from plone.protect.interfaces import IAuthenticatorView
from plone.protect.utils import protect
from zope.deprecation import deprecated


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


def check(request):
    if isinstance(request, HTTPRequest):
        if not _verify(request):
            raise Forbidden('Form authenticator is invalid.')


def AuthenticateForm(callable):
    return protect(check)(callable)

deprecated("AuthenticateForm", "Please use the plone.protect.protect decorator")


__all__ = [ "AuthenticatorView", "AuthenticateForm", "check" ]

