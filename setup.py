# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup


version = '3.0.25'

setup(
    name='plone.protect',
    version=version,
    description="Security for browser forms",
    long_description='%s\n%s' % (
        open("README.rst").read(),
        open("CHANGES.rst").read()
    ),
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Framework :: Plone :: 5.0",
        "Framework :: Plone :: 5.1",
        "Framework :: Zope2",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
    ],
    keywords='zope security CSRF',
    author='Plone Foundation',
    author_email='plone-developers@lists.sourceforge.net',
    url='https://pypi.python.org/pypi/plone.protect',
    license='BSD',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['plone', ],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'plone.keyring >= 3.0dev',
        'zope.component',
        'zope.interface',
        'Zope2',
        'plone.transformchain',
        'repoze.xmliter>=0.3',
        'five.globalrequest',
        'collective.monkeypatcher'
    ],
    extras_require={
        'test': [
            'plone.app.testing',
            'Products.CMFPlone'
        ],
    }
)
