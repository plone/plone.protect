Introduction
============

This package contains utilities that can help to protect parts of Plone
or applications build on top of the Plone framework.


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

You can do the same thing more conveniently using a function decorator::

  from plone.app.protect.authenticator import AuthenticateForm

  @AuthenticateForm
  def manage_doSomething(self, param, REQUEST=None):
      pass

This only works for methods which have a parameter called REQUEST.


