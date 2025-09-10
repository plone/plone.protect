from plone.protect.auto import safeWrite
from zope.testing.cleanup import addCleanUp

import inspect


def wl_lockmapping(self, killinvalids=0, create=0):
    has_write_locks = hasattr(self, "_dav_writelocks")
    locks = self._old_wl_lockmapping(killinvalids=killinvalids, create=create)
    try:
        safeWrite(locks)
        if not has_write_locks and create:
            # first time writing to object, need to mark it safe
            safeWrite(self)
    except AttributeError:
        # not a persistent class, ignore
        pass
    return locks


def pluggableauth__getCSRFToken(request):
    """
    let plone.protect do it's job
    """
    return ""


def pluggableauth__checkCSRFToken(request, token="csrf_token", raises=True):
    """
    let plone.protect do it's job
    """
    pass


def marmoset_patch(func, replacement):
    source = inspect.getsource(replacement)
    exec(source, func.__globals__)
    func._old_code = func.__code__
    func.__code__ = replacement.__code__


def disable_zope_csrf_checks():
    from Products.PluggableAuthService import utils as pluggable_utils

    if hasattr(pluggable_utils, "checkCSRFToken"):
        marmoset_patch(
            pluggable_utils.checkCSRFToken,
            pluggableauth__checkCSRFToken,
        )
    if hasattr(pluggable_utils, "getCSRFToken"):
        marmoset_patch(pluggable_utils.getCSRFToken, pluggableauth__getCSRFToken)


def enable_zope_csrf_checks():
    from Products.PluggableAuthService import utils as pluggable_utils

    if hasattr(pluggable_utils, "checkCSRFToken"):
        try:
            pluggable_utils.checkCSRFToken.__code__ = (
                pluggable_utils.checkCSRFToken._old_code
            )
        except AttributeError:
            pass
    if hasattr(pluggable_utils, "getCSRFToken"):
        try:
            pluggable_utils.getCSRFToken.__code__ = (
                pluggable_utils.getCSRFToken._old_code
            )
        except AttributeError:
            pass


addCleanUp(enable_zope_csrf_checks)
