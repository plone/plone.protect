Introduction
============

This package contains utilities that can help protect parts of Plone
or applications build on top of the Plone framework.


1. Restricting to HTTP POST
===========================

a) Using decorator
------------------

If you only need to allow HTTP POST requests you can use the *PostOnly*
checker::

  from plone.protect import PostOnly
  from plone.protect import protect

  @protect(PostOnly)
  def manage_doSomething(self, param, REQUEST=None):
      pass

This checker operates only on HTTP requests; other types of requests
are not checked.

b) Passing request to a function validator
------------------------------------------

Simply::

    from plone.protect import PostOnly

    ...
    PostOnly(self.context.REQUEST)
    ...

2. Form authentication (CSRF)
=============================

A common problem in web applications is Cross Site Request Forgery or CSRF.
This is an attack method in which an attacker tricks a browser to do a HTTP
form submit to another site. To do this the attacker needs to know the exact
form parameters. Form authentication is a method to make it impossible for an
attacker to predict those parameters by adding an extra authenticator which
can be verified.

Generating the token
--------------------

To use the form authenticator you first need to insert it into your form.
This can be done using a simple TAL statement inside your form::

  <span tal:replace="structure context/@@authenticator/authenticator"/>

this will produce a HTML input element with the authentication information.

If you want to create the token value programmatically, use the following::

    from plone.protect.authenticator import createToken
    token = createToken()

Validating the token
--------------------

a) Zope Component Architecture way
**********************************

Next you need to add logic somewhere to verify the authenticator. This
can be done using a call to the authenticator view. For example::

   authenticator=getMultiAdapter((context, request), name=u"authenticator")
   if not authenticator.verify():
       raise Unauthorized

b) Using decorator
******************

You can do the same thing more conveniently using the ``protect`` decorator::

  from plone.protect import CheckAuthenticator
  from plone.protect import protect

  @protect(CheckAuthenticator)
  def manage_doSomething(self, param, REQUEST=None):
      pass

c) Passing request to a function validator
******************************************

Or just::

    from plone.protect import CheckAuthenticator

    ...
    CheckAuthenticator(self.context.REQUEST)
    ...

Headers
-------

You can also pass in the token by using the header ``X-CSRF-TOKEN``. This can be
useful for AJAX requests.


Protect decorator
=================

The most common way to use plone.protect is through the ``protect``
decorator. This decorator takes a list of *checkers* as parameters: each
checker will check a specific security aspect of the request. For example::

  from plone.protect import protect
  from plone.protect import PostOnly

  @protect(PostOnly)
  def SensitiveMethod(self, REQUEST=None):
      # This is only allowed with HTTP POST requests.

This **relies** on the protected method having a parameter called **REQUEST (case sensitive)**.

Customized Form Authentication
------------------------------

If you'd like use a different authentication token for different forms,
you can provide an extra string to use with the token::

  <tal:authenticator tal:define="authenticator context/@@authenticator">
    <span tal:replace="structure python: authenticator.authenticator('a-form-related-value')"/>
  </tal:authenticator>

To verify::

  authenticator=getMultiAdapter((context, request), name=u"authenticator")
  if not authenticator.verify('a-form-related-value'):
      raise Unauthorized

With the decorator::

  from plone.protect import CustomCheckAuthenticator
  from plone.protect import protect

  @protect(CustomCheckAuthenticator('a-form-related-value'))
  def manage_doSomething(self, param, REQUEST=None):
      pass


Automatic CSRF Protection
=========================

Since version 3, plone.protect provides automatic CSRF protection. It does
this by automatically including the auth token to all internal forms when
the user requesting the page is logged in.

Additionally, whenever a particular request attempts to write to the ZODB,
it'll check for the existence of a correct auth token.


Allowing write on read programmatically
---------------------------------------

When you need to allow a known write on read, you've got several options.

Adding a CSRF token to your links
**********************************

If you've got a GET request that causes a known write on read, your first
option should be to simply add a CSRF token to the URLs that result in that
request. ``plone.protect`` provides the ``addTokenToUrl`` function for this
purpose::

    from plone.protect.utils import addTokenToUrl

    url = addTokenToUrl(url)


If you just want to allow an object to be writable on a request...
******************************************************************

You can use the ``safeWrite`` helper function::

    from plone.protect.utils import safeWrite

    safeWrite(myobj, request)


Marking the entire request as safe
**********************************

Just add the ``IDisableCSRFProtection`` interface to the current request
object::

    from plone.protect.interfaces import IDisableCSRFProtection
    from zope.interface import alsoProvides

    alsoProvides(request, IDisableCSRFProtection)

Warning! When you do this, the current request is susceptible to CSRF
exploits so do any required CSRF protection manually.


Clickjacking Protection
=======================

plone.protect also provides, by default, clickjacking protection since
version 3.0.

To protect against this attack, Plone uses the X-Frame-Options
header. plone.protect will set the X-Frame-Options value to ``SAMEORIGIN``.

To customize this value, you can set it to a custom value for a custom view
(e.g. ``self.request.response.setHeader('X-Frame-Options', 'ALLOWALL')``),
override it at your proxy server, or you can set the environment variable of
``PLONE_X_FRAME_OPTIONS`` to whatever value you'd like plone.protect to set
this to globally.

You can opt out of this by making the environment variable empty.


Disable All Automatic CSRF Protection
=====================================

To disable all automatic CSRF protection, set the environment variable
``PLONE_CSRF_DISABLED`` value to ``true``.

.. Warning::

   It is very dangerous to do this. Do not do this unless the ZEO client
   with this setting is not public and you know what you are doing.

.. Note::
   This doesn't disable explicit and manual CSRF protection checks.


Fixing CSRF Protection failures in tests
========================================

If you get ``Unauthorized`` errors in tests due to unprotected form submission
where normally automatic protection would be in place you can use the following
blueprint to protect your forms::

    from plone.protect.authenticator import createToken
    from ..testing import MY_INTEGRATION_TESTING_LAYER
    import unittest

    class MyTest(unittest.TestCase):

        layer = MY_INTEGRATION_TESTING_LAYER

        def setUp(self):
            self.request = self.layer['request']
            # Disable plone.protect for these tests
            self.request.form['_authenticator'] = createToken()
            # Eventuelly you find this also useful
            self.request.environ['REQUEST_METHOD'] = 'POST'


Notes
=====

This package monkey patches a number of modules in order to better handle CSRF
protection::

  - Archetypes add forms, add csrf
  - Zope2 object locking support
  - pluggable auth csrf protection

If you are using a proxy cache in front of your site, be aware that
you will need to clear the entry for ``++resource++protect.js`` every
time you update this package or you will find issues with modals while
editing content.


Compatibility
=============

``plone.protect`` version 3 was made for Plone 5.  You can use it on
Plone 4 for better protection, but you will need the
``plone4.csrffixes`` hotfix package as well to avoid getting
needless warnings or errors.  See the `hotfix announcement`_ and the
`hotfix page`_.

.. _`hotfix announcement`: https://plone.org/products/plone/security/advisories/security-vulnerability-20151006-csrf
.. _`hotfix page`: https://plone.org/products/plone-hotfix/releases/20151006
