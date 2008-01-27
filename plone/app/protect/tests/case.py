from unittest import TestCase
from zope.component import getGlobalSiteManager
from zope.interface import implements
from plone.keyring.interfaces import IKeyManager

class MockKeyManager:
    implements(IKeyManager)

    keys = [ "one", "two", "three", "four", "five" ]

    def secret(self):
        return self.keys[0]

    def __getitem__(self, key):
        return self.keys


class KeyringTestCase(TestCase):
    def setUp(self):
        self.sm=getGlobalSiteManager()
        self.manager=MockKeyManager()
        self.sm.registerUtility(self.manager, provided=IKeyManager, event=False)

    def tearDown(self):
        self.sm.unregisterUtility(self.manager, provided=IKeyManager)

