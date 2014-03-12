from Acquisition import aq_parent
from plone.keyring.interfaces import IKeyManager
from plone.protect.interfaces import IDisableCSRFProtection
from Products.PluggableAuthService.interfaces.events import IUserLoggedInEvent
from zope.component import ComponentLookupError
from zope.component import adapter
from zope.component import getUtility
from zope.component import getSiteManager
from zope.component.hooks import getSite
from zope.interface import alsoProvides

import time
import logging
LOGGER = logging.getLogger('plone.protect')

_ring_rotation_schedules = (
    ('_system', 60 * 60 * 24 * 7),  # weekly
    ('_forms', 60 * 60 * 24),  # daily
    ('_anon', 60 * 60 * 24),  # daily
)


def _rotate(manager):
    current_time = time.time()
    for ring_name, check_period in _ring_rotation_schedules:
        try:
            ring = manager[ring_name]
            if (ring.last_rotation + check_period) < current_time:
                LOGGER.info('auto rotating keyring %s' % ring_name)
                ring.rotate()
        except KeyError:
            continue


@adapter(IUserLoggedInEvent)
def onUserLogsIn(event):
    """
    since we already write to the database when a user logs in,
    let's check for key rotation here
    """
    try:
        # disable csrf protection on login requests
        req = event.object.REQUEST
        alsoProvides(req, IDisableCSRFProtection)
    except AttributeError:
        req = None

    try:
        manager = getUtility(IKeyManager)
        _rotate(manager)
        # also check rotation of zope root keyring
        app = aq_parent(getSite())
        sm = getSiteManager(app)
        manager = sm.getUtility(IKeyManager)
        if manager:
            _rotate(manager)
    except ComponentLookupError:
        if req:
            url = req.URL
        else:
            url = ''
        LOGGER.warn('cannot find key manager for url %s' % url)
