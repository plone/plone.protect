import hmac
import sys
from unittest import TestSuite
from unittest import makeSuite
from AccessControl import getSecurityManager
from zExceptions import Forbidden
from ZPublisher.HTTPRequest import HTTPRequest
from plone.protect.tests.case import KeyringTestCase
from plone.protect.tests.case import MockRequest
from plone.protect.authenticator import AuthenticatorView
from plone.protect.authenticator import check
from plone.protect import protect
from plone.protect import CustomCheckAuthenticator
from plone.protect import createToken

try:
    from hashlib import sha1 as sha
except ImportError:
    import sha


class AuthenticatorTests(KeyringTestCase):

    def setUp(self):
        KeyringTestCase.setUp(self)
        self.view = AuthenticatorView(None, None)

    def setUsername(self, name):
        user = getSecurityManager().getUser()
        user.name = name

    def setSecret(self, secret):
        self.manager['_forms'].data[0] = secret

    def testIsHtmlInput(self):
        auth = self.view.authenticator()
        self.failUnless(auth.startswith("<input"))
        self.failUnless(auth.endswith("/>"))

    def testDiffersPerUser(self):
        one = self.view.authenticator()
        self.setUsername("other")
        two = self.view.authenticator()
        self.assertNotEqual(one, two)

    def testDiffersPerSecret(self):
        one = self.view.authenticator()
        self.setSecret("other")
        two = self.view.authenticator()
        self.assertNotEqual(one, two)

    def testDiffersPerExtra(self):
        one = self.view.authenticator()
        two = self.view.authenticator('some-extra-value')
        self.assertNotEqual(one, two)


class VerifyTests(KeyringTestCase):

    key_size = 2

    def setUp(self):
        self.request = MockRequest()
        super(VerifyTests, self).setUp()
        self.view = AuthenticatorView(None, self.request)

    def setAuthenticator(self, key, extra='', name="_authenticator"):
        user = getSecurityManager().getUser().getUserName()
        auth = hmac.new(key, user + extra, sha).hexdigest()
        self.request[name] = auth

    def testCorrectAuthenticator(self):
        self.manager['_forms'].data[0] = "secret"
        self.setAuthenticator("secret")
        self.assertEqual(self.view.verify(), True)

    def testCustomAuthenticatorKeyName(self):
        self.manager['_forms'].data[0] = "secret"
        self.setAuthenticator("secret", name="_my_authenticator")
        self.assertEqual(self.view.verify(name="_my_authenticator"), True)

    def testOlderSecretVerifies(self):
        self.manager['_forms'].data[1] = "backup"
        self.setAuthenticator("backup")
        self.assertEqual(self.view.verify(), True)

    def testMissingAuthenticator(self):
        self.assertEqual(self.view.verify(), False)

    def testIncorrectAuthenticator(self):
        self.request["_authenticator"] = "incorrect"
        self.assertEqual(self.view.verify(), False)

    def testAuthenticatorWrongType(self):
        self.request["_authenticator"] = 123
        self.assertEqual(self.view.verify(), False)

    def testExtraArgumentCanBeVerified(self):
        self.manager['_forms'].data[0] = "secret"
        self.setAuthenticator("secret", 'some-extra-value')
        self.assertEqual(self.view.verify('some-extra-value'), True)


class DecoratorTests(KeyringTestCase):

    def setUp(self):
        self.request = HTTPRequest(sys.stdin, dict(SERVER_URL="dummy"), None)
        KeyringTestCase.setUp(self)

        def func(REQUEST=None):
            return 1
        self.func = protect(check)(func)

    def testNoRequestParameter(self):

        def func():
            pass
        self.assertRaises(ValueError, protect(check), func)

    def testIgnoreBadRequestType(self):
        self.assertEqual(self.func(), 1)

    def testBadAuthenticator(self):
        self.request["_authenticator"] = "incorrect"
        self.assertRaises(Forbidden, self.func, self.request)

    def testAuthenticatedCustom(self):
        self.request['_authenticator'] = createToken('some-value')

        def func(REQUEST=self.request):
            return True
        self.assertEquals(
            protect(CustomCheckAuthenticator('some-value'))(func)(), True)

    def testAuthenticatedCustomName(self):
        self.request['_my_authenticator'] = createToken('some-value')

        def func(REQUEST=self.request):
            return True
        self.assertEquals(
            protect(CustomCheckAuthenticator(
                'some-value', '_my_authenticator'))(func)(), True)


def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(AuthenticatorTests))
    suite.addTest(makeSuite(VerifyTests))
    suite.addTest(makeSuite(DecoratorTests))
    return suite
