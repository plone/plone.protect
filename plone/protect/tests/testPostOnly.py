from unittest import TestCase
from unittest import TestSuite
from unittest import makeSuite
from plone.protect.postonly import check
from ZPublisher.HTTPRequest import HTTPRequest
from zExceptions import Forbidden


class PostOnlyTests(TestCase):

    def makeRequest(self, method):
        return HTTPRequest(None,
                           dict(REQUEST_METHOD=method,
                                SERVER_PORT="80",
                                SERVER_NAME="localhost"),
                           None)

    def testNonHTTPRequestAllowed(self):
        check("not a request")

    def testGETRequestForbidden(self):
        self.assertRaises(Forbidden, check, self.makeRequest("GET"))

    def testPOSTRequestAllowed(self):
        check(self.makeRequest("POST"))


def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(PostOnlyTests))
    return suite
