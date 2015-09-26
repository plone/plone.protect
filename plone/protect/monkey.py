from urlparse import urlparse, urljoin
from plone.protect.auto import safeWrite
import inspect
from Products.PluggableAuthService import utils as pluggable_utils


def RedirectTo__call__(self, controller_state):
    url = self.getArg(controller_state)
    context = controller_state.getContext()
    # see if this is a relative url or an absolute
    if len(urlparse(url)[1]) == 0:
        # No host specified, so url is relative.  Get an absolute url.
        url = urljoin(context.absolute_url()+'/', url)
    url = self.updateQuery(url, controller_state.kwargs)
    request = context.REQUEST
    # this is mostly just for archetypes edit forms...
    if 'edit' in url and '_authenticator' not in url and \
            '_authenticator' in request.form:
        if '?' in url:
            url += '&'
        else:
            url += '?'
        auth = request.form['_authenticator']
        if isinstance(auth, list):
            auth = auth[0]
        url += '_authenticator=' + auth
    return request.RESPONSE.redirect(url)


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
    marmoset_patch(pluggable_utils.checkCSRFToken, pluggableauth__checkCSRFToken)
if hasattr(pluggable_utils, 'getCSRFToken'):
    marmoset_patch(pluggable_utils.getCSRFToken, pluggableauth__getCSRFToken)