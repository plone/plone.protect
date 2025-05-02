from setuptools import find_packages
from setuptools import setup


version = "5.0.4"

setup(
    name="plone.protect",
    version=version,
    description="Security for browser forms",
    long_description="{}\n{}".format(
        open("README.rst").read(), open("CHANGES.rst").read()
    ),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 6.0",
        "Framework :: Plone :: Core",
        "Framework :: Zope :: 5",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="zope security CSRF",
    author="Plone Foundation",
    author_email="plone-developers@lists.sourceforge.net",
    url="https://github.com/plone/plone.protect",
    license="BSD",
    packages=find_packages(),
    namespace_packages=[
        "plone",
    ],
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "collective.monkeypatcher",
        "lxml[cssselect]",
        "plone.keyring",
        "plone.scale",
        "plone.transformchain",
        "Products.CMFCore",
        "Products.GenericSetup",
        "Products.PluggableAuthService",
        "repoze.xmliter",
        "setuptools",
        "z3c.zcmlhook",
        "Zope",
    ],
    extras_require={
        "test": [
            "plone.app.testing",
            "plone.testing",
        ],
    },
)
