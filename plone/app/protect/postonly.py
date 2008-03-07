from ZPublisher.HTTPRequest import HTTPRequest
from zExceptions import Forbidden


def check(request):
    if isinstance(request, HTTPRequest):
        if request.get('REQUEST_METHOD', 'GET').upper() != 'POST':
            raise Forbidden('Request must be POST')
