from plone.protect.interfaces import IConfirmView
from Products.Five import BrowserView
from zope.interface import implementer


@implementer(IConfirmView)
class ConfirmView(BrowserView):
    pass
