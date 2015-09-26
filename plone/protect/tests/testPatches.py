from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.protect.testing import PROTECT_FUNCTIONAL_TESTING
from plone.testing.z2 import Browser
import unittest2 as unittest


class TestCSRF(unittest.TestCase):
    layer = PROTECT_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.browser = Browser(self.layer['app'])
        self.request = self.layer['request']
        self.browser.addHeader(
            'Authorization', 'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD,))

    def test_change_password_on_root_does_not_throw_other_csrf_protection(self):
        self.browser.open('%s/acl_users/users/manage_users?user_id=%s&passwd=1' % (
            self.layer['app'].absolute_url(), SITE_OWNER_NAME))
        self.browser.getControl(name='password').value = SITE_OWNER_PASSWORD
        self.browser.getControl(name='confirm').value = SITE_OWNER_PASSWORD
        self.browser.getForm().submit()
        self.assertEquals(
            self.browser.url,
            '%s/acl_users/users/manage_users?manage_tabs_message=password+updated' % (
                self.layer['app'].absolute_url()))