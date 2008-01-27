import os
from setuptools import setup, find_packages

version = '1.0'

setup(name='plone.app.protect',
      version=version,
      description="Security for browser forms",
      long_description=open("README.txt").read() + "\n" + \
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Framework :: Zope3",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='plone security CSFS',
      author='Wichert Akkerman',
      author_email='plone-developers@lists.sourceforge.net',
      url='http://svn.plone.org/svn/plone/plone.app.example',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone.app'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          "plone.keyring",
      ],
      )
