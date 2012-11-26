Introduction
============

This package contains utilities that can help to protect parts of Plone
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

This checker only operators on HTTP requests; other types of requests
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

Validating the token
--------------------

a) ZCA way
**********

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
-------------------------------

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
