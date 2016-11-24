# -*- coding: utf-8 -*-
from plone.protect.auto import safeWrite
from Products.PluggableAuthService import utils as pluggable_utils

import inspect


def wl_lockmapping(self, killinvalids=0, create=0):
    has_write_locks = hasattr(self, '_dav_writelocks')
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
    return ''


def pluggableauth__checkCSRFToken(request, token='csrf_token', raises=True):
    """
    let plone.protect do it's job
    """
    pass


def marmoset_patch(func, replacement):
    source = inspect.getsource(replacement)
    exec source in func.func_globals
    func.func_code = replacement.func_code


# otherwise the patches do not get applied in some cases
if hasattr(pluggable_utils, 'checkCSRFToken'):
    marmoset_patch(pluggable_utils.checkCSRFToken,
                   pluggableauth__checkCSRFToken)
if hasattr(pluggable_utils, 'getCSRFToken'):
    marmoset_patch(pluggable_utils.getCSRFToken, pluggableauth__getCSRFToken)
