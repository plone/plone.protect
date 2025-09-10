from plone.protect.authenticator import createToken
from plone.protect.testing import PROTECT_FUNCTIONAL_TESTING
from zExceptions import Forbidden
from zope.component import getMultiAdapter

import unittest


class TestAttackVector(unittest.TestCase):
    layer = PROTECT_FUNCTIONAL_TESTING

    def test_regression(self):
        portal = self.layer["portal"]
        request = self.layer["request"]
        view = getMultiAdapter((portal, request), name="confirm-action")
        request.form.update({"original_url": "foobar", "_authenticator": createToken()})
        self.assertTrue('value="foobar"' in view())

    def test_valid_url(self):
        portal = self.layer["portal"]
        request = self.layer["request"]
        view = getMultiAdapter((portal, request), name="confirm-action")
        request.form.update(
            {"original_url": "javascript:alert(1)", "_authenticator": createToken()}
        )
        self.assertRaises(Forbidden, view)

    def test_valid_authenticator(self):
        portal = self.layer["portal"]
        request = self.layer["request"]
        view = getMultiAdapter((portal, request), name="confirm-action")
        request.form.update(
            {"original_url": portal.absolute_url(), "_authenticator": "foobar"}
        )

        with self.assertRaises(Forbidden) as cm:
            view()
        self.assertEqual(str(cm.exception), "Form authenticator is invalid.")
