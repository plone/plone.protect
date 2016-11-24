# -*- coding: utf-8 -*-
from plone.protect.interfaces import IConfirmView
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from zExceptions import Forbidden
from zope.interface import implementer


@implementer(IConfirmView)
class ConfirmView(BrowserView):

    def __call__(self):
        urltool = getToolByName(self.context, 'portal_url')
        original_url = getattr(self.request, 'original_url', '')
        if not original_url or not urltool.isURLInPortal(original_url):
            raise Forbidden('url not in portal')
        return self.index()
