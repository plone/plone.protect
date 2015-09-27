from setuptools import setup, find_packages

version = '3.0.9'

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
        "Framework :: Zope2",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    keywords='zope security CSRF',
    author='Plone Foundation',
    author_email='plone-developers@lists.sourceforge.net',
    url='http://pypi.python.org/pypi/plone.protect',
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
