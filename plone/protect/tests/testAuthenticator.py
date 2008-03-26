import hmac
import sha
import sys
from unittest import TestSuite
from unittest import makeSuite
from AccessControl import getSecurityManager
from zExceptions import Forbidden
from ZPublisher.HTTPRequest import HTTPRequest
from plone.protect.tests.case import KeyringTestCase
from plone.protect.authenticator import AuthenticatorView
from plone.protect.authenticator import AuthenticateForm



class AuthenticatorTests(KeyringTestCase):
    def setUp(self):
        KeyringTestCase.setUp(self)
        self.view=AuthenticatorView(None, None)


    def setUsername(self, name):
        user=getSecurityManager().getUser()
        user.name=name


    def setSecret(self, secret):
        self.manager.keys[0]=secret


    def testIsHtmlInput(self):
        auth=self.view.authenticator()
        self.failUnless(auth.startswith("<input"))
        self.failUnless(auth.endswith("/>"))


    def testConsistent(self):
        one=self.view.authenticator()
        two=self.view.authenticator()
        self.assertEqual(one, two)


    def testDiffersPerUser(self):
        one=self.view.authenticator()
        self.setUsername("other")
        two=self.view.authenticator()
        self.assertNotEqual(one, two)


    def testDiffersPerSecret(self):
        one=self.view.authenticator()
        self.setSecret("other")
        two=self.view.authenticator()
        self.assertNotEqual(one, two)



class VerifyTests(KeyringTestCase):
    def setUp(self):
        self.request={}
        KeyringTestCase.setUp(self)
        self.view=AuthenticatorView(None, self.request)


    def setAuthenticator(self, key):
        user=getSecurityManager().getUser().getUserName()
        auth=hmac.new(key, user, sha).hexdigest()
        self.request["_authenticator"]=auth


    def testCorrectAuthenticator(self):
        self.manager.keys[0]=("secret")
        self.setAuthenticator("secret")
        self.assertEqual(self.view.verify(), True)


    def testOlderSecretVerifies(self):
        self.manager.keys[3]="backup"
        self.setAuthenticator("backup")
        self.assertEqual(self.view.verify(), True)


    def testMissingAuthenticator(self):
        self.assertEqual(self.view.verify(), False)


    def testIncorrectAuthenticator(self):
        self.request["_authenticator"]="incorrect"
        self.assertEqual(self.view.verify(), False)


    def testAuthenticatorWrongType(self):
        self.request["_authenticator"]=123
        self.assertEqual(self.view.verify(), False)



class DecoratorTests(KeyringTestCase):
    def setUp(self):
        self.request=HTTPRequest(sys.stdin, dict(SERVER_URL="dummy"), None)
        KeyringTestCase.setUp(self)
        def func(REQUEST=None):
            return 1
        self.func=AuthenticateForm(func)


    def testNoRequestParameter(self):
        def func():
            pass
        self.assertRaises(ValueError, AuthenticateForm, func)


    def testIgnoreBadRequestType(self):
        self.assertEqual(self.func(), 1)


    def testBadAuthenticator(self):
        self.request["_authenticator"]="incorrect"
        self.assertRaises(Forbidden, self.func, self.request)


def test_suite():
    suite=TestSuite()
    suite.addTest(makeSuite(AuthenticatorTests))
    suite.addTest(makeSuite(VerifyTests))
    suite.addTest(makeSuite(DecoratorTests))
    return suite
