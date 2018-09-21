# -*- coding: utf-8 -*-
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.keyring.interfaces import IKeyManager
from plone.protect import createToken
from plone.protect.authenticator import AuthenticatorView
from plone.protect.auto import ProtectTransform
from plone.protect.auto import safeWrite
from plone.protect.testing import PROTECT_FUNCTIONAL_TESTING
from plone.testing.z2 import Browser
from zExceptions import Forbidden
from zope.component import getUtility

import transaction
import unittest


class _BaseAutoTest(object):
    layer = PROTECT_FUNCTIONAL_TESTING

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
        except Exception:
            pass

    def test_does_not_add_csrf_protection_to_different_domain_scheme_relative(
            self):
        self.open('test-unprotected')
        form = self.browser.getForm('four')
        try:
            form.getControl(name="_authenticator")
            self.assertEqual('should not add authenticator', '')
        except Exception:
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
        # except Exception as ex:
        #     self.assertEquals(ex.getcode(), 403)
        self.browser.getControl('submit1').click()
        self.assertFalse(hasattr(self.portal, "foo"))


class AutoCSRFProtectTests(unittest.TestCase, _BaseAutoTest):

    def setUp(self):
        self.portal = self.layer['portal']
        self.browser = Browser(self.layer['app'])
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        self.browser.open(self.portal.absolute_url() + '/login_form')
        self.browser.getControl(name='__ac_name').value = TEST_USER_NAME
        self.browser.getControl(
            name='__ac_password'
        ).value = TEST_USER_PASSWORD
        self.browser.getControl('Log in').click()

    def open(self, path):
        self.browser.open(self.portal.absolute_url() + '/' + path)

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


class TestRoot(unittest.TestCase, _BaseAutoTest):

    def setUp(self):
        self.portal = self.layer['portal']
        self.browser = Browser(self.layer['app'])
        self.request = self.layer['request']
        self.browser.addHeader(
            'Authorization',
            'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD,)
        )

    def open(self, path):
        self.browser.open(self.portal.aq_parent.absolute_url() + '/' + path)


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
        self.browser.getControl('Log in').click()

        self.assertNotEqual(keys, ring.data)
        self.assertNotEqual(ring.last_rotation, 0)


class TestAutoChecks(unittest.TestCase):
    layer = PROTECT_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.request.REQUEST_METHOD = 'POST'

    def test_safe_write_empty_returns_false(self):
        transform = ProtectTransform(self.portal, self.request)
        transform._registered_objects = lambda: [self.portal]
        self.assertRaises(Forbidden, transform._check)

    def test_safe_write_empty_returns_true(self):
        safeWrite(self.portal, self.request)
        transform = ProtectTransform(self.portal, self.request)
        transform._registered_objects = lambda: [self.portal]
        self.assertTrue(transform._check())


class TestAutoTransform(unittest.TestCase):
    layer = PROTECT_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.request.response.setHeader('Content-Type', 'text/html')
        self.request.REQUEST_METHOD = 'POST'

    def test_empty_no_error(self):
        # empty pages (eg. tiles or ajax requests) should not lead to
        # transform errors or warnings
        transform = ProtectTransform(self.portal, self.request)
        result = transform.transform(['\n'], 'utf-8')
        self.assertEqual(result, None)

    def test_html(self):
        transform = ProtectTransform(self.portal, self.request)
        result = transform.transform([(
            '<html>\n<body>'
            '<form action="http://nohost/myaction" method="POST">'
            '</form></body>\n</html>')], 'utf-8')
        self.failUnless(b'_authenticator' in result.serialize())


class SecurityHeadersTestCase(unittest.TestCase):
    """Test case to check security headers are added."""

    layer = PROTECT_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.request.response.setHeader('Content-Type', 'text/html')

    def test_x_frame_options(self):
        # default value
        header = 'x-frame-options'
        transform = ProtectTransform(self.portal, self.request)
        transform.transformIterable(['\n'], 'utf-8')
        response = self.request.response
        self.assertIn(header, response.headers)
        self.assertEqual(response.getHeader(header), 'SAMEORIGIN')

        # if a value is already set, the header respects it
        response.setHeader(header, 'foo')
        transform.transformIterable(['\n'], 'utf-8')
        self.assertIn(header, response.headers)
        self.assertEqual(response.getHeader(header), 'foo')

    def test_x_xss_protection(self):
        # default value
        header = 'x-xss-protection'
        transform = ProtectTransform(self.portal, self.request)
        transform.transformIterable(['\n'], 'utf-8')
        response = self.request.response
        self.assertIn(header, response.headers)
        self.assertEqual(response.getHeader(header), '1; mode=block')

        # if a value is already set, the header respects it
        response.setHeader(header, 'foo')
        transform.transformIterable(['\n'], 'utf-8')
        self.assertIn(header, response.headers)
        self.assertEqual(response.getHeader(header), 'foo')

    def test_x_content_type_options(self):
        # default value
        header = 'x-content-type-options'
        transform = ProtectTransform(self.portal, self.request)
        transform.transformIterable(['\n'], 'utf-8')
        response = self.request.response
        self.assertIn(header, response.headers)
        self.assertEqual(response.getHeader(header), 'nosniff')

        # if a value is already set, the header respects it
        response.setHeader(header, 'foo')
        transform.transformIterable(['\n'], 'utf-8')
        self.assertIn(header, response.headers)
        self.assertEqual(response.getHeader(header), 'foo')
