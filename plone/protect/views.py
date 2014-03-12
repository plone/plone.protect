from plone.protect.interfaces import IConfirmView
from Products.Five import BrowserView
from zope.interface import implements


class ConfirmView(BrowserView):
    implements(IConfirmView)
