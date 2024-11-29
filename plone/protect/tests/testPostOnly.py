from plone.protect.postonly import check
from unittest import defaultTestLoader
from unittest import TestCase
from unittest import TestSuite
from zExceptions import Forbidden
from ZPublisher.HTTPRequest import HTTPRequest


class PostOnlyTests(TestCase):
    def makeRequest(self, method):
        return HTTPRequest(
            None,
            dict(REQUEST_METHOD=method, SERVER_PORT="80", SERVER_NAME="localhost"),
            None,
        )

    def testNonHTTPRequestAllowed(self):
        check("not a request")

    def testGETRequestForbidden(self):
        self.assertRaises(Forbidden, check, self.makeRequest("GET"))

    def testPOSTRequestAllowed(self):
        check(self.makeRequest("POST"))


def test_suite():
    return TestSuite((defaultTestLoader.loadTestsFromTestCase(PostOnlyTests),))
