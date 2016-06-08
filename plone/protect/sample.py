import logging
from Products.Five import BrowserView

logger = logging.getLogger('sample')


class Sample(BrowserView):

    def __call__(self):
        existing = getattr(self.context, 'sample_value', '')
        logger.info('Existing value: %s', existing)
        value = self.request.get('value', '')
        self.context.sample_value = value
        msg = 'old %s new %s' % (existing, value)
        return msg
