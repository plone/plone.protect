from unittest import TestCase
from zope.component import getGlobalSiteManager
from plone.keyring.interfaces import IKeyManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.User import User
from plone.keyring.keymanager import KeyManager


class MockRequest(dict):

    def __init__(self, URL=None, *args, **kwargs):
        super(MockRequest, self).__init__(*args, **kwargs)
        self.environ = {}
        self.URL = URL

    def setReferer(self, url):
        self.environ['HTTP_REFERER'] = url

    def getHeader(self, name):
        return None


class KeyringTestCase(TestCase):

    key_size = 1

    def setUp(self):
        self.sm = getGlobalSiteManager()
        self.manager = KeyManager(self.key_size)
        self.sm.registerUtility(self.manager, provided=IKeyManager,
                                event=False)
        # Tests modify the user object so we better make sure it is *our*
        # user object and not the built-in Anonymous User.
        newSecurityManager(None, User('dummy', 'secret', (), ()))

    def tearDown(self):
        self.sm.unregisterUtility(self.manager, provided=IKeyManager)
        noSecurityManager()
