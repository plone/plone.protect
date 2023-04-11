from AccessControl import getSecurityManager
from Acquisition import aq_parent
from BTrees.OOBTree import OOBTree
from lxml import etree
from lxml import html
from plone.keyring.interfaces import IKeyManager
from plone.protect.authenticator import check
from plone.protect.authenticator import createToken
from plone.protect.authenticator import isAnonymousUser
from plone.protect.interfaces import IConfirmView
from plone.protect.interfaces import IDisableCSRFProtection
from plone.protect.utils import getRoot
from plone.protect.utils import getRootKeyManager
from plone.protect.utils import SAFE_WRITE_KEY
from plone.protect.utils import safeWrite  # noqa b/w compat import
from plone.scale.storage import ScalesDict
from plone.transformchain.interfaces import ITransform
from Products.CMFCore.utils import getToolByName
from repoze.xmliter.serializer import XMLSerializer
from repoze.xmliter.utils import getHTMLSerializer
from urllib.parse import urlencode
from urllib.parse import urlparse
from zExceptions import Forbidden
from zope.component import adapter
from zope.component import ComponentLookupError
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.interface import implementer
from zope.interface import Interface

import itertools
import logging
import os
import traceback
import transaction
import types


# do not hard depend here on plone.portlets (for Plone 7)
try:
    from plone.portlets.interfaces import IPortletAssignment
except ImportError:
    IPortletAssignment = None

logger = logging.getLogger("plone.protect")

X_FRAME_OPTIONS = os.environ.get("PLONE_X_FRAME_OPTIONS", "SAMEORIGIN")
CSRF_DISABLED = os.environ.get("PLONE_CSRF_DISABLED", "false").lower() in (
    "true",
    "t",
    "yes",
    "y",
    "1",
)
ANNOTATION_KEYS = (
    "plone.contentrules.localassignments",
    "syndication_settings",
    "plone.portlets.contextassignments",
    "plone.scale",
)
SAFE_TYPES = (ScalesDict,)


@implementer(ITransform)
@adapter(Interface, Interface)  # any context, any request
class ProtectTransform:
    """
    XXX Need to be extremely careful with everything we do in here
    since an error here would mean the transform is skipped
    and no CSRF protection...
    """

    # should be last lxml related transform
    order = 9000

    key_manager = None
    site = None
    safe_views = ("plone_lock_operations",)

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def parseTree(self, result, encoding):
        # if it's a redirect, the result shall not be transformed
        request = self.request

        if request.response.status in (301, 302):
            return None

        if isinstance(result, XMLSerializer):
            return result

        # hhmmm, this is kind of taken right out of plone.app.theming
        # maybe this logic(parsing dom) should be someone central?
        contentType = self.request.response.getHeader("Content-Type")
        if contentType is None or not contentType.startswith("text/html"):
            return None

        contentEncoding = self.request.response.getHeader("Content-Encoding")
        if contentEncoding and contentEncoding in (
            "zip",
            "deflate",
            "compress",
        ):
            return None

        if isinstance(result, list) and len(result) == 1:
            # do not parse empty strings to omit warning log message
            if not result[0].strip():
                return None
        try:
            result = getHTMLSerializer(result, pretty_print=False, encoding=encoding)
            # We are going to force html output here always as XHTML
            # output does odd character encodings
            result.serializer = html.tostring
            return result
        except (AttributeError, TypeError, etree.ParseError):
            # XXX handle something special?
            logger.warn(
                "error parsing dom, failure to add csrf "
                "token to response for url %s" % self.request.URL
            )
            return None

    def transformBytes(self, result, encoding):
        result = result.decode(encoding, "ignore")
        return self.transformIterable([result], encoding)

    def transformString(self, result, encoding):
        return self.transformIterable([result], encoding)

    def transformUnicode(self, result, encoding):
        return self.transformIterable([result], encoding)

    def transformIterable(self, result, encoding):
        """Apply the transform if required"""
        # before anything, do the clickjacking protection
        if X_FRAME_OPTIONS and not self.request.response.getHeader("X-Frame-Options"):
            self.request.response.setHeader("X-Frame-Options", X_FRAME_OPTIONS)

        if CSRF_DISABLED:
            return

        # only auto CSRF protect authenticated users
        if isAnonymousUser(getSecurityManager().getUser()):
            return

        # if on confirm view, do not check, just abort and
        # immediately transform without csrf checking again
        if IConfirmView.providedBy(self.request.get("PUBLISHED")):
            # abort it, show the confirmation...
            transaction.abort()
            return self.transform(result, encoding)

        # next, check if we're a resource not connected
        # to a ZODB object--no context
        context = self.getContext()
        if not context:
            return

        try:
            tool = getToolByName(context, "portal_url", None)
            if tool:
                self.site = tool.getPortalObject()
        except TypeError:
            self.site = getSite()

        try:
            self.key_manager = getUtility(IKeyManager)
        except ComponentLookupError:
            root = getRoot(context)
            self.key_manager = getRootKeyManager(root)

        if self.site is None and self.key_manager is None:
            # key manager not installed and no site object.
            # key manager must not be installed on site root, ignore
            return

        if not self.check():
            # we don't need to transform the doc, we're getting redirected
            return

        # finally, let's run the transform
        return self.transform(result, encoding)

    def getContext(self):
        published = self.request.get("PUBLISHED")
        if isinstance(published, types.MethodType):
            return published.__self__
        return aq_parent(published)

    def getViewName(self):
        try:
            return self.getContext().__name__
        except AttributeError:
            return None

    def check(self):
        """
        just being very careful here about our check so we don't
        cause errors that prevent this check from happening
        """
        try:
            return self._check()
        except Exception:
            transaction.abort()
            logger.error(
                "Error checking for CSRF. "
                "Transaction will be aborted since the request "
                "is now unsafe:\n%s" % (traceback.format_exc())
            )
            raise

    def _registered_objects(self):
        app = self.request.PARENTS[-1]
        return list(
            itertools.chain.from_iterable(
                [
                    conn._registered_objects
                    # skip the 'temporary' connection since it stores session objects
                    # which get written all the time
                    for name, conn in app._p_jar.connections.items()
                    if name != "temporary"
                ]
            )
        )

    def _check(self):
        registered = self._registered_objects()
        if len(registered) > 0 and not IDisableCSRFProtection.providedBy(self.request):
            if self.getViewName() in self.safe_views:
                return True
            # Okay, we're writing here, we need to protect!
            try:
                check(self.request, manager=self.key_manager)
                return True
            except ComponentLookupError:
                logger.info(
                    "Can not find key manager for CSRF protection. "
                    "This should not happen."
                )
                raise
            except Forbidden:
                # XXX
                # okay, so right now, we're going to check if the current
                # registered objects to write, are just portlet assignments.
                # I don't know why, but when a site is created, these
                # cause some writes on read. ALL, registered objects
                # need to be portlet assignments. XXX needs to be fixed
                # somehow...
                safe_oids = []
                if SAFE_WRITE_KEY in getattr(self.request, "environ", {}):
                    safe_oids = self.request.environ[SAFE_WRITE_KEY]
                safe = True
                for obj in registered:
                    if (
                        IPortletAssignment is not None
                        and IPortletAssignment.providedBy(obj)
                    ):
                        continue
                    if getattr(obj, "_p_oid", False) in safe_oids:
                        continue
                    if SAFE_TYPES and isinstance(obj, SAFE_TYPES):
                        continue
                    if isinstance(obj, OOBTree):
                        safe = False
                        for key in ANNOTATION_KEYS:
                            try:
                                if key in obj:
                                    safe = True
                                    break
                            except TypeError:
                                pass
                        if safe:
                            continue
                    safe = False
                    break
                if not safe:
                    if self.request.REQUEST_METHOD != "GET":
                        # only try to be "smart" with GET requests
                        raise
                    logger.info(
                        "{:s}\naborting transaction due to no CSRF "
                        "protection on url {:s}".format(
                            "\n".join(traceback.format_stack()), self.request.URL
                        )
                    )
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
                    ct = resp.getHeader("Content-Type", "") or ""
                    if self.site and (resp.status in (301, 302) or "text/html" in ct):
                        data = self.request.form.copy()
                        data["original_url"] = self.request.URL
                        resp.redirect(
                            "{}/@@confirm-action?{}".format(
                                self.site.absolute_url(), urlencode(data)
                            )
                        )
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

    def transform(self, result, encoding):
        result = self.parseTree(result, encoding)
        if result is None:
            return None
        root = result.tree.getroot()
        url = urlparse(self.request.URL)
        try:
            token = createToken(manager=self.key_manager)
        except ComponentLookupError:
            if self.site is not None:
                logger.warn(
                    "Keyring not found on site. This should not happen", exc_info=True
                )
            return result

        for form in root.cssselect("form"):
            # XXX should we only do POST? If we're logged in and
            # it's an internal form, I'm inclined to say no...
            # method = form.attrib.get('method', 'GET').lower()
            # if method != 'post':
            #    continue

            # some get forms we definitely do not want to protect.
            # for now, we know search we do not want to protect
            method = form.attrib.get("method", "GET").lower()
            action = form.attrib.get("action", "").strip()
            if method == "get" and "@@search" in action:
                continue
            action = form.attrib.get("action", "").strip()
            if not self.isActionInSite(action, url):
                continue
            # check if the token is already on the form..
            hidden = form.cssselect('[name="_authenticator"]')
            if len(hidden) == 0:
                hidden = etree.Element("input")
                hidden.attrib["name"] = "_authenticator"
                hidden.attrib["type"] = "hidden"
                hidden.attrib["value"] = token
                form.append(hidden)

        if self.site is not None and not root.cssselect("#protect-script"):
            # Alternative: add this in the resource registry.
            site_url = self.site.absolute_url()
            elements = root.cssselect("body")
            if len(elements):
                body = elements[0]
                protect_script = etree.Element("script")
                protect_script.attrib.update(
                    {
                        "type": "application/javascript",
                        "src": "%s/++resource++protect.js" % site_url,
                        "data-site-url": site_url,
                        "data-token": token,
                        "id": "protect-script",
                    }
                )
                body.append(protect_script)

        return result
