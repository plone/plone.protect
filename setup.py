from setuptools import setup, find_packages

version = '2.0.2'

setup(name='plone.protect',
      version=version,
      description="Security for browser forms",
      long_description=open("README.rst").read() + "\n" + \
                       open("CHANGES.txt").read(),
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
          'plone.keyring > 1.0',
          'zope.component',
          'zope.interface',
          'Zope2',
      ],
      )
