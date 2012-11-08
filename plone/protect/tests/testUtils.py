from unittest import TestCase
from unittest import TestSuite
from unittest import makeSuite
from plone.protect.utils import protect
from zope.globalrequest import setRequest


def func(one, two):
    return (one, two)


class DummyChecker:

    def __call__(self, request):
        self.request = request


class DecoratorTests(TestCase):

    def testArgumentsPassed(self):
        wrapped = protect()(func)
        self.assertEqual(wrapped("one", "two"), ("one", "two"))

    def testKeywordArguments(self):
        wrapped = protect()(func)
        self.assertEqual(wrapped(one="one", two="two"), ("one", "two"))

    def testMixedArguments(self):
        wrapped = protect()(func)
        self.assertEqual(wrapped("one", two="two"), ("one", "two"))

    def testRequestPassedToChecker(self):
        checker = DummyChecker()
        wrapped = protect(checker)(func)
        request = []
        setRequest(request)
        wrapped("one", "two")
        self.failUnless(checker.request is request)

    def testUnboundMethod(self):
        class TestClass(object):
            def method(self, one, two):
                return (one, two)
        TestClass.method = protect()(TestClass.method)
        self.assertEqual(TestClass().method("one", "two"), ("one", "two"))


def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(DecoratorTests))
    return suite
