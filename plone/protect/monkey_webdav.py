# -*- coding: utf-8 -*-
from plone.protect.auto import safeWrite


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
