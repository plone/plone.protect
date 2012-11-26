from unittest import TestCase
from zope.component import getGlobalSiteManager
from zope.interface import implements
from plone.keyring.interfaces import IKeyManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.User import User


class MockRequest(dict):

    def __init__(self, URL=None, *args, **kwargs):
        super(MockRequest, self).__init__(*args, **kwargs)
        self.environ = {}
        self.URL = URL

    def setReferer(self, url):
        self.environ['HTTP_REFERER'] = url


class MockKeyManager:
    implements(IKeyManager)

    keys = ["one", "two", "three", "four", "five"]

    def secret(self):
        return self.keys[0]

    def __getitem__(self, key):
        return self.keys


class KeyringTestCase(TestCase):

    def setUp(self):
        self.sm = getGlobalSiteManager()
        self.manager = MockKeyManager()
        self.sm.registerUtility(self.manager,
            provided=IKeyManager, event=False)
        # Tests modify the user object so we better make sure it is *our*
        # user object and not the built-in Anonymous User.
        newSecurityManager(None, User('dummy', 'secret', (), ()))

    def tearDown(self):
        self.sm.unregisterUtility(self.manager, provided=IKeyManager)
        noSecurityManager()
