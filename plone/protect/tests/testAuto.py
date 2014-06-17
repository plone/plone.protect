import unittest2 as unittest
import transaction

from plone.testing.z2 import Browser
from plone.protect.testing import PROTECT_FUNCTIONAL_TESTING

from plone.protect import createToken
from plone.protect.authenticator import AuthenticatorView
from plone.keyring.interfaces import IKeyManager
from zope.component import getUtility
from plone.app.testing import logout
from plone.app.testing import login
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD


class AutoCSRFProtectTests(unittest.TestCase):
    layer = PROTECT_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.browser = Browser(self.layer['app'])
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        self.open('login_form')
        self.browser.getControl(name='__ac_name').value = TEST_USER_NAME
        self.browser.getControl(
            name='__ac_password').value = TEST_USER_PASSWORD
        self.browser.getControl(name='submit').click()

    def open(self, path):
        self.browser.open(self.portal.absolute_url() + '/' + path)

    def test_adds_csrf_protection_input(self):
        self.open('test-unprotected')
        self.assertTrue('name="_authenticator"' in self.browser.contents)

    def test_adds_csrf_protection_for_scheme_relative_same_domain(self):
        self.open('test-unprotected')
        form = self.browser.getForm('five')
        form.getControl(name="_authenticator")

    def test_adds_csrf_protection_for_relative_path(self):
        self.open('test-unprotected')
        form = self.browser.getForm('seven')
        form.getControl(name="_authenticator")

    def test_adds_csrf_protection_for_no_action(self):
        self.open('test-unprotected')
        form = self.browser.getForm('one')
        form.getControl(name="_authenticator")

    def test_does_not_add_csrf_protection_to_different_domain(self):
        self.open('test-unprotected')
        form = self.browser.getForm('six')
        try:
            form.getControl(name="_authenticator")
            self.assertEqual('should not add authenticator', '')
        except:
            pass

    def test_does_not_add_csrf_protection_to_different_domain_scheme_relative(
            self):
        self.open('test-unprotected')
        form = self.browser.getForm('four')
        try:
            form.getControl(name="_authenticator")
            self.assertEqual('should not add authenticator', '')
        except:
            pass

    def test_authentication_works_automatically(self):
        self.open('test-unprotected')
        self.browser.getControl('submit1').click()
        self.assertEqual(self.portal.foo, "bar")

    def test_authentication_works_for_other_form(self):
        self.open('test-unprotected')
        self.browser.getControl('submit2').click()
        self.assertEqual(self.portal.foo, "bar")

    def test_works_for_get_form_yet(self):
        self.open('test-unprotected')
        self.browser.getControl('submit3').click()

    def test_forbidden_raised_if_auth_failure(self):
        self.open('test-unprotected')
        self.browser.getForm('one').\
            getControl(name="_authenticator").value = 'foobar'
        # XXX: plone.transformchain don't reraise exceptions
        # try:
        #    self.browser.getControl('submit1').click()
        # except Exception, ex:
        #     self.assertEquals(ex.getcode(), 403)
        self.browser.getControl('submit1').click()
        self.assertFalse(hasattr(self.portal, "foo"))

    def test_CSRF_header(self):
        self.request.environ['HTTP_X_CSRF_TOKEN'] = createToken()
        view = AuthenticatorView(None, self.request)
        self.assertEqual(view.verify(), True)

    def test_incorrect_CSRF_header(self):
        self.request.environ['HTTP_X_CSRF_TOKEN'] = 'foobar'
        view = AuthenticatorView(None, self.request)
        self.assertEqual(view.verify(), False)

    def test_only_add_auth_when_user_logged_in(self):
        logout()
        self.open('logout')
        self.open('test-unprotected')
        try:
            self.browser.getForm('one').getControl(name="_authenticator")
            self.assertEqual('anonymous should not be protected', '')
        except LookupError:
            pass


class AutoRotateTests(unittest.TestCase):
    layer = PROTECT_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.browser = Browser(self.layer['app'])
        self.request = self.layer['request']

    def test_keyrings_get_rotated_on_login(self):
        manager = getUtility(IKeyManager)
        ring = manager['_forms']
        keys = ring.data
        ring.last_rotation = 0
        transaction.commit()

        # should be rotated on login
        login(self.portal, TEST_USER_NAME)
        self.browser.open(self.portal.absolute_url() + '/login_form')
        self.browser.getControl(name='__ac_name').value = TEST_USER_NAME
        self.browser.getControl(
            name='__ac_password').value = TEST_USER_PASSWORD
        self.browser.getControl(name='submit').click()

        self.assertNotEqual(keys, ring.data)
        self.assertNotEqual(ring.last_rotation, 0)
