# -*- coding: utf-8 -*-
#
# File: MeetingNamur.py
#
# Copyright (c) 2017 by Imio.be
# Generator: ArchGenXML Version 2.7
#            http://plone.org/products/archgenxml
#
# GNU General Public License (GPL)
#

__author__ = """Andre Nuyens <andre@imio.be>"""
__docformat__ = 'plaintext'


# Product configuration.
#
# The contents of this module will be imported into __init__.py, the
# workflow configuration and every content type module.
#
# If you wish to perform custom configuration, you may put a file
# AppConfig.py in your product's root directory. The items in there
# will be included (by importing) in this file if found.

from Products.CMFCore.permissions import setDefaultRoles

PROJECTNAME = "MeetingNamur"

# Permissions
WriteDescription = 'MeetingNamur: Write description'
#  for test, we must give writeDescription for Member
setDefaultRoles(WriteDescription, ('Manager', 'Member'))
WriteCertified = 'MeetingNamur: Write certified signatures'
setDefaultRoles(WriteCertified, ('Manager',))

product_globals = globals()

# Dependencies of Products to be installed by quick-installer
# override in custom configuration
DEPENDENCIES = []

# Dependend products - not quick-installed - used in testcase
# override in custom configuration
PRODUCT_DEPENDENCIES = []

STYLESHEETS = [{'id': 'meetingnamur.css',
                'title': 'MeetingNamur CSS styles'}]
