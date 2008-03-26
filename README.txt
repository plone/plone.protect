Introduction
============

This package contains utilities that can help to protect parts of Plone
or applications build on top of the Plone framework.


protect decorator
=================

The most common way to use plone.protect is through the ``protect``
decorator. This decorator takes a list of *checkers* as parameters: each
checker will check a specific security aspect of the request. For example::

  from plone.protect import protect
  from plone.protect import PostOnly

  @protect(PostOnly)
  def SensitiveMethod(self, REQUEST=None):
      # This is only allowed with HTTP POST requests.

This relies on the protected method having a parameter called REQUEST.

HTTP POST
=========

If you only need to allow HTTP POST requests you can use the *PostOnly*
checker::

  from plone.protect import PostOnly
  from plone.protect import protect

  @protect(PostOnly)
  def manage_doSomething(self, param, REQUEST=None):
      pass

This checker only operators on HTTP requests; other types of requests
are not checked.


Form authentication
===================

A common problem in web applications is Cross Site Request Forgery or CSRF.
This is an attack method in which an attacker tricks a browser to do a HTTP
form submit to another site. To do this the attacker needs to know the exact
form parameters. Form authentication is a method to make it impossible for an
attacker to predict those parameters by adding an extra authenticator which
can be verified.

To use the form authenticator you first need to insert it into your form.
This can be done using a simple TAL statement inside your form::

  <span tal:replace="structure context/@@authenticator/authenticator"/>

this will produce a HTML input element with the authentication information.
Next you need to add logic somewhere to verify the authenticator. This
can be done using a call to the authenticator view. For example::

   authenticator=getMultiAdapter((request, context), name=u"authenticator")
   if not authenticator.verify():
       raise Unauthorized

You can do the same thing more conveniently using the ``protect`` decorator::

  from plone.protect import CheckAuthenticator
  from plone.protect import protect

  @protect(CheckAuthenticator)
  def manage_doSomething(self, param, REQUEST=None):
      pass



