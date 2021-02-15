from setuptools import setup, find_packages
import os

version = '4.1'

setup(name='Products.MeetingNamur',
      version=version,
      description="PloneMeeting profile for city of Namur",
      long_description=open("README.rst").read() + "\n" + open("CHANGES.rst").read(),
      classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
      ],
      keywords='',
      author='Andre Nuyens',
      author_email='andre.nuyens@imio.be',
      url='http://www.imio.be/produits/gestion-des-deliberations',
      license='GPL',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      extras_require=dict(
          test=['Products.PloneMeeting[test]']),
      install_requires=[
          'Products.MeetingCommunes'],
      entry_points={},
      )
