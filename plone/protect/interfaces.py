from zope.interface import Interface


class IAuthenticatorView(Interface):

    def token():
        """return token value"""

    def authenticator():
        """Return an xhtml snippet which sets an authenticator.

        This must be included inside a <form> element.
        """

    def verify():
        """
        Verify if the request contains a valid authenticator.
        """


class IDisableCSRFProtection(Interface):
    """Be able to disable on a per-request basis.

    In this version of plone.protect it does nothing.

    Forward port from plone.protect 3, so you do not need code like this
    when you want to disable csrf protection:

        try:
            from plone.protect.interfaces import IDisableCSRFProtection
        except ImportError:
            IDisableCSRFProtection = None
        if IDisableCSRFProtection is not None:
            alsoProvides(request, IDisableCSRFProtection)
    """
