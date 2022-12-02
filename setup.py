# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup


version = '4.1.7'

setup(
    name='plone.protect',
    version=version,
    description="Security for browser forms",
    long_description='%s\n%s' % (
        open("README.rst").read(),
        open("CHANGES.rst").read()
    ),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 5.2",
        "Framework :: Plone :: 6.0",
        "Framework :: Plone :: Core",
        "Framework :: Zope :: 2",
        "Framework :: Zope :: 4",
        "Framework :: Zope :: 5",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords='zope security CSRF',
    author='Plone Foundation',
    author_email='plone-developers@lists.sourceforge.net',
    url='https://github.com/plone/plone.protect',
    license='BSD',
    packages=find_packages(),
    namespace_packages=['plone', ],
    include_package_data=True,
    zip_safe=False,
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*,!=3.5.*',
    install_requires=[
        'lxml[cssselect]',
        'setuptools',
        'plone.keyring >= 3.0dev',
        'six',
        'zope.component',
        'zope.interface',
        'Zope2',
        'plone.transformchain',
        'repoze.xmliter>=0.3',
        'collective.monkeypatcher',
        'z3c.zcmlhook',
    ],
    extras_require={
        'test': [
            'plone.app.testing',
            'Products.CMFPlone'
            'zope.annotation',
        ],
    }
)
