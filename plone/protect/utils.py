from AccessControl.requestmethod import buildfacade
from Acquisition import aq_parent
from BTrees.IFBTree import IFBTree
from BTrees.IIBTree import IIBTree
from BTrees.IOBTree import IOBTree
from BTrees.LFBTree import LFBTree
from BTrees.LLBTree import LLBTree
from BTrees.LOBTree import LOBTree
from BTrees.OIBTree import OIBTree
from BTrees.OLBTree import OLBTree
from BTrees.OOBTree import OOBTree
from OFS.interfaces import IApplication
from plone.keyring.keymanager import KeyManager
from plone.protect.authenticator import createToken
from zope.globalrequest import getRequest

import inspect
import logging


SAFE_WRITE_KEY = "plone.protect.safe_oids"
BTREE_TYPES = (
    IFBTree,
    IIBTree,
    IOBTree,
    LFBTree,
    LLBTree,
    LOBTree,
    OIBTree,
    OLBTree,
    OOBTree,
)
LOGGER = logging.getLogger("plone.protect")

_default = []

# This is based on AccessControl.requestmethod.postonly
# It should probably be updated to use the decorator module.


class protect:
    def __init__(self, *checkers):
        self.checkers = checkers

    def __call__(self, callable):
        try:
            spec = inspect.getfullargspec(callable)
        except AttributeError:
            # Python 2.7 compatibility
            spec = inspect.getargspec(callable)

        args = spec.args
        defaults = spec.defaults

        try:
            r_index = args.index("REQUEST")
        except ValueError:
            raise ValueError("No REQUEST parameter in callable signature")

        arglen = len(args)
        if defaults is not None:
            defaults = list(zip(args[arglen - len(defaults) :], defaults))
            arglen -= len(defaults)

        def _curried(*args, **kw):
            request = None

            if len(args) > r_index:
                request = args[r_index]

            for checker in self.checkers:
                checker(request)

            # Reconstruct keyword arguments
            if defaults is not None:
                args, kwparams = args[:arglen], args[arglen:]
                for positional, (key, default) in zip(kwparams, defaults):
                    if positional is _default:
                        kw[key] = default
                    else:
                        kw[key] = positional

            return callable(*args, **kw)

        # Build a facade, with a reference to our locally-scoped _curried
        facade_globs = dict(_curried=_curried, _default=_default)
        name = callable.__name__
        exec(buildfacade(name, callable, callable.__doc__), facade_globs)
        return facade_globs[name]


def addTokenToUrl(url, req=None, manager=None):
    if not url:
        return url
    if req is None:
        req = getRequest()
    if req is None or not url.startswith(req.SERVER_URL):
        # only transforms urls to same site
        return url
    if getattr(req, "environ", _default) is _default:
        # TestRequests have no environ.
        token = createToken(manager=manager)
    elif "_auth_token" not in req.environ:
        # Let's cache this value since this could be called
        # many times for one request.
        token = createToken(manager=manager)
        req.environ["_auth_token"] = token
    else:
        token = req.environ["_auth_token"]

    if "_authenticator" not in url:
        if "?" not in url:
            url += "?"
        else:
            url += "&"
        url += "_authenticator=" + token
    return url


def getRootKeyManager(root):
    if not IApplication.providedBy(root):
        return
    try:
        manager = root._key_manager
    except AttributeError:
        manager = root._key_manager = KeyManager()
        safeWrite(root._key_manager)
        safeWrite(root)
    return manager


def getRoot(context):
    while not IApplication.providedBy(context) and context is not None:
        context = aq_parent(context)
    return context


def safeWrite(obj, request=None):
    if request is None:
        request = getRequest()
    if request is None or getattr(request, "environ", _default) is _default:
        # Request not found or it is a TestRequest without an environment.
        LOGGER.debug("could not mark object as a safe write")
        return
    if SAFE_WRITE_KEY not in request.environ:
        request.environ[SAFE_WRITE_KEY] = []
    try:
        if obj._p_oid not in request.environ[SAFE_WRITE_KEY]:
            request.environ[SAFE_WRITE_KEY].append(obj._p_oid)
        if isinstance(obj, BTREE_TYPES):
            bucket = obj._firstbucket
            while bucket:
                if bucket._p_oid not in request.environ[SAFE_WRITE_KEY]:
                    request.environ[SAFE_WRITE_KEY].append(bucket._p_oid)
                bucket = bucket._next
    except AttributeError:
        LOGGER.debug("object you attempted to mark safe does not have an oid")
