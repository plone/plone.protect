from Products.Five import BrowserView
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing.layers import FunctionalTesting
from plone.protect.auto import safeWrite
from zope.configuration import xmlconfig


class ProtectedLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # load ZCML
        import plone.protect
        xmlconfig.file('configure.zcml', plone.protect,
                       context=configurationContext)
        xmlconfig.file('test.zcml', plone.protect.tests,
                       context=configurationContext)

    def setUpPloneSite(self, portal):
        # install into the Plone site
        applyProfile(portal, 'plone.protect:default')
        self.portal = portal


PROTECT_FIXTURE = ProtectedLayer()
PROTECT_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PROTECT_FIXTURE,), name="PROTECT_FIXTURE:Functional")


class TestUnprotectedView(BrowserView):

    def __call__(self):
        # on posts, write something to the db
        if 'submit1' in self.request.form or 'submit2' in self.request.form:
            self.context.foo = 'bar'
            self.context._p_changed = True
        return """
<html>
<body>
<form id="one" method="POST">
    <input type="submit" name="submit1" value="submit1" />
</form>
<form id="two" action="%s" METHOD="post">
    <input type="submit" name="submit2" value="submit2" />
</form>
<form id="three" method="GET">
    <input type="submit" name="submit3" value="submit3" />
</form>
<form id="four" action="//foobar/somepath.php" method="POST">
    <input type="submit" name="submit4" value="submit4" />
</form>
<form id="five" action="//nohost/plone" method="POST">
    <input type="submit" name="submit5" value="submit5" />
</form>
<form id="six" action="https://foobar/somepath.php" method="POST">
    <input type="submit" name="submit6" value="submit6" />
</form>
<form id="seven" action="a/relative/path" method="POST">
    <input type="submit" name="submit7" value="submit7" />
</form>
</body>
</html>""" % (
            self.request.URL,
        )

class TestSafeToWriteObject(BrowserView):
    def __call__(self):
        self.context.foo = 'bar'
        safeWrite(self)
        return 'done'
