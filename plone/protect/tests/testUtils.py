from unittest import TestCase
from unittest import TestSuite
from unittest import makeSuite
from plone.protect.utils import protect

def funcWithoutRequest():
    pass

def funcWithRequest(one, two, REQUEST=None):
    return (one, two)

class DummyChecker:
    def __call__(self, request):
        self.request=request

class DecoratorTests(TestCase):
    def testFunctionMustHaveRequest(self):
        protector=protect()
        self.assertRaises(ValueError, protector, funcWithoutRequest)

    def testArgumentsPassed(self):
        wrapped=protect()(funcWithRequest)
        self.assertEqual(wrapped("one", "two"), ("one", "two"))

    def testKeywordArguments(self):
        wrapped=protect()(funcWithRequest)
        self.assertEqual(wrapped(one="one", two="two"), ("one", "two"))

    def testMixedArguments(self):
        wrapped=protect()(funcWithRequest)
        self.assertEqual(wrapped("one", two="two"), ("one", "two"))

    def testRequestPassedToChecker(self):
        checker=DummyChecker()
        wrapped=protect(checker)(funcWithRequest)
        request=[]
        wrapped("one", "two", request)
        self.failUnless(checker.request is request)



def test_suite():
    suite=TestSuite()
    suite.addTest(makeSuite(DecoratorTests))
    return suite
