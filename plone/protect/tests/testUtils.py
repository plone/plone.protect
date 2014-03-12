from unittest import TestCase
from unittest import TestSuite
from unittest import makeSuite
from plone.protect.utils import protect, addTokenToUrl
import unittest2 as unittest
from plone.protect.testing import PROTECT_FUNCTIONAL_TESTING


def funcWithoutRequest():
    pass


def funcWithRequest(one, two, REQUEST=None):
    return (one, two)


class DummyChecker:

    def __call__(self, request):
        self.request = request


class DecoratorTests(TestCase):

    def testFunctionMustHaveRequest(self):
        protector = protect()
        self.assertRaises(ValueError, protector, funcWithoutRequest)

    def testArgumentsPassed(self):
        wrapped = protect()(funcWithRequest)
        self.assertEqual(wrapped("one", "two"), ("one", "two"))

    def testKeywordArguments(self):
        wrapped = protect()(funcWithRequest)
        self.assertEqual(wrapped(one="one", two="two"), ("one", "two"))

    def testMixedArguments(self):
        wrapped = protect()(funcWithRequest)
        self.assertEqual(wrapped("one", two="two"), ("one", "two"))

    def testRequestPassedToChecker(self):
        checker = DummyChecker()
        wrapped = protect(checker)(funcWithRequest)
        request = []
        wrapped("one", "two", request)
        self.failUnless(checker.request is request)


class UrlTests(unittest.TestCase):

    layer = PROTECT_FUNCTIONAL_TESTING

    def testWithUrlFromSameDomain(self):
        url = addTokenToUrl('http://nohost/foobar', self.layer['request'])
        self.failUnless('_authenticator=' in url)

    def testWithUrlFromOtherDomain(self):
        url = addTokenToUrl('http://other/foobar', self.layer['request'])
        self.failUnless('_authenticator=' not in url)

    def testAddingWithQueryParams(self):
        url = addTokenToUrl('http://nohost/foobar?foo=bar',
                            self.layer['request'])
        self.failUnless('_authenticator=' in url)

    def testWithoutRequest(self):
        url = addTokenToUrl('http://nohost/foobar')
        self.failUnless('_authenticator=' in url)

    def testWithNone(self):
        url = addTokenToUrl(None, self.layer['request'])
        self.failUnless(not url)


def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(DecoratorTests))
    suite.addTest(makeSuite(UrlTests))
    return suite
