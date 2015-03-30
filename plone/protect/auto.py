from AccessControl import getSecurityManager
from Acquisition import aq_parent
from lxml import etree
from OFS.interfaces import IApplication
from plone.portlets.interfaces import IPortletAssignment
from plone.protect.authenticator import check
from plone.protect.authenticator import createToken
from plone.protect.authenticator import isAnonymousUser
from plone.protect.interfaces import IConfirmView
from plone.protect.interfaces import IDisableCSRFProtection
from plone.keyring.interfaces import IKeyManager
from plone.transformchain.interfaces import ITransform
from repoze.xmliter.utils import getHTMLSerializer
import transaction
from zExceptions import Forbidden
from zope.component import adapts
from zope.component.hooks import getSite
from zope.component import getUtility
from zope.component import ComponentLookupError
from zope.interface import implements, Interface

from urlparse import urlparse
from urllib import urlencode
import itertools
import os
import traceback
import logging
LOGGER = logging.getLogger('plone.protect')


X_FRAME_OPTIONS = os.environ.get('PLONE_X_FRAME_OPTIONS', 'SAMEORIGIN')
CSRF_DISABLED = os.environ.get('PLONE_CSRF_DISABLED', 'false') == 'true'


class ProtectTransform(object):
    """
    XXX Need to be extremely careful with everything we do in here
    since an error here would mean the transform is skipped
    and no CSRF protection...
    """

    implements(ITransform)
    adapts(Interface, Interface)  # any context, any request

    # should be last lxml related transform
    order = 9000

    key_manager = None
    site = None

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def parseTree(self, result):
        # hhmmm, this is kind of taken right out of plone.app.theming
        # maybe this logic(parsing dom) should be someone central?
        contentType = self.request.response.getHeader('Content-Type')
        if contentType is None or not contentType.startswith('text/html'):
            return None

        contentEncoding = self.request.response.getHeader('Content-Encoding')
        if contentEncoding and contentEncoding in ('zip', 'deflate',
                                                   'compress',):
            return None

        try:
            return getHTMLSerializer(result, pretty_print=False)
        except (TypeError, etree.ParseError):
            # XXX handle something special?
            LOGGER.warn('error parsing dom, failure to add csrf '
                        'token to response for url %s' % self.request.URL)
            return None

    def transformBytes(self, result, encoding):
        result = unicode(result, encoding, 'ignore')
        return self.transformIterable([result], encoding)

    def transformString(self, result, encoding):
        return self.transformIterable([result], encoding)

    def transformUnicode(self, result, encoding):
        return self.transformIterable([result], encoding)

    def transformIterable(self, result, encoding):
        """Apply the transform if required
        """
        # before anything, do the clickjacking protection
        self.request.response.setHeader('X-Frame-Options', X_FRAME_OPTIONS)

        if CSRF_DISABLED:
            return

        # only auto CSRF protect authenticated users
        if isAnonymousUser(getSecurityManager().getUser()):
            return

        # if on confirm view, do not check, just abort and
        # immediately transform without csrf checking again
        if IConfirmView.providedBy(self.request.get('PUBLISHED')):
            # abort it, show the confirmation...
            transaction.abort()
            return self.transform(result)

        # next, check if we're a resource not connected
        # to a ZODB object--no context
        context = self.getContext()
        if not context:
            return

        self.site = getSite()
        try:
            self.key_manager = getUtility(IKeyManager)
        except ComponentLookupError:
            pass

        if self.site is None and self.key_manager is None:
            # key manager not installed and no site object.
            # key manager must not be installed on site root, ignore
            return

        if not self.check():
            # we don't need to transform the doc, we're getting redirected
            return

        # finally, let's run the transform
        return self.transform(result)

    def getContext(self):
        published = self.request.get('PUBLISHED')
        return aq_parent(published)

    def check(self):
        """
        just being very careful here about our check so we don't
        cause errors that prevent this check from happening
        """
        try:
            return self._check()
        except:
            transaction.abort()
            LOGGER.error("Error checking for CSRF. "
                         "Transaction will be aborted since the request "
                         "is now unsafe:\n%s" % (
                             traceback.format_exc()))
            raise

    def _registered_objects(self):
        app = self.request.PARENTS[-1]
        return list(itertools.chain.from_iterable([
            conn._registered_objects
            for conn in app._p_jar.connections.values()
        ]))

    def _check(self):
        if len(self._registered_objects()) > 0 and \
                not IDisableCSRFProtection.providedBy(self.request):
            # Okay, we're writing here, we need to protect!
            try:
                check(self.request)
                return True
            except ComponentLookupError:
                # okay, it's possible we're at the zope root and the KeyManager
                # hasn't been installed yet. Let's check and carry on
                # if this is the case
                if IApplication.providedBy(self.getContext()):
                    LOGGER.info('skipping csrf protection on zope root until '
                                'keymanager gets installed')
                    return True
                raise
            except Forbidden:
                if self.request.REQUEST_METHOD != 'GET':
                    # only try to be "smart" with GET requests
                    raise

                # XXX
                # okay, so right now, we're going to check if the current
                # registered objects to write, are just portlet assignments.
                # I don't know why, but when a site is created, these
                # cause some writes on read. ALL, registered objects
                # need to be portlet assignments. XXX needs to be fixed
                # somehow...
                all_portlet_assignments = True
                for obj in self._registered_objects():
                    if not IPortletAssignment.providedBy(obj):
                        all_portlet_assignments = False
                        break
                if not all_portlet_assignments:
                    LOGGER.info('aborting transaction due to no CSRF '
                                'protection on url %s' % self.request.URL)
                    transaction.abort()

                    # conditions for doing the confirm form are:
                    #   1. 301, 302 response code
                    #   2. text/html response
                    #   3. getSite could be none, zope root maybe, carry on
                    # otherwise,
                    #   just abort with a log entry because we tried to
                    #   write on read, without a POST request and we don't
                    #   know what to do with it gracefully.
                    resp = self.request.response
                    ct = resp.headers.get('content-type')
                    if self.site and (
                            resp.status in (301, 302) or 'text/html' in ct):
                        data = self.request.form.copy()
                        data['original_url'] = self.request.URL
                        resp.redirect('%s/@@confirm-action?%s' % (
                            self.site.absolute_url(),
                            urlencode(data)
                        ))
                        return False
        return True

    def isActionInSite(self, action, current_url):
        # sanitize url
        url = urlparse(action)
        if not url.hostname:
            # no hostname means this is relative
            return True
        if url.hostname != current_url.hostname:
            return False
        return True

    def transform(self, result):
        result = self.parseTree(result)
        if result is None:
            return None
        root = result.tree.getroot()
        url = urlparse(self.request.URL)
        try:
            token = createToken()
        except ComponentLookupError:
            if self.site is None:
                # skip here, utility not installed yet on zope root
                return
            raise

        for form in root.cssselect('form'):
            # XXX should we only do POST? If we're logged in and
            # it's an internal form, I'm inclined to say no...
            # method = form.attrib.get('method', 'GET').lower()
            # if method != 'post':
            #    continue

            # some get forms we definitely do not want to protect.
            # for now, we know search we do not want to protect
            method = form.attrib.get('method', 'GET').lower()
            action = form.attrib.get('action', '').strip()
            if method == 'get' and '@@search' in action:
                continue
            action = form.attrib.get('action', '').strip()
            if not self.isActionInSite(action, url):
                continue
            # check if the token is already on the form..
            hidden = form.cssselect('[name="_authenticator"]')
            if len(hidden) == 0:
                hidden = etree.Element("input")
                hidden.attrib['name'] = '_authenticator'
                hidden.attrib['type'] = 'hidden'
                hidden.attrib['value'] = token
                form.append(hidden)

        return result

    def __call__(self, result, encoding):
        if CSRF_DISABLED:
            return result
        if isinstance(result, unicode):
            newResult = self.transformUnicode(result, encoding)
        elif isinstance(result, str):
            newResult = self.transformBytes(result, encoding)
        else:
            newResult = self.transformIterable(result, encoding)

        if newResult is not None:
            result = newResult

        return result
