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
    """
    Be able to disable on a per-request basis
    """


class IConfirmView(Interface):
    pass
