# -*- coding: utf-8 -*-

from Products.CMFCore.permissions import setDefaultRoles
from Products.PloneMeeting import config as PMconfig


PROJECTNAME = "MeetingNamur"

# Permissions
WriteDescription = 'MeetingNamur: Write description'
#  for test, we must give writeDescription for Member
setDefaultRoles(WriteDescription, ('Manager', 'Member'))
WriteCertified = 'MeetingNamur: Write certified signatures'
setDefaultRoles(WriteCertified, ('Manager',))

product_globals = globals()

STYLESHEETS = [{'id': 'meetingnamur.css',
                'title': 'MeetingNamur CSS styles'}]

PMconfig.EXTRA_GROUP_SUFFIXES = [
    {'fct_title': u'budgetimpactreviewers',
     'fct_id': u'budgetimpactreviewers',
     'fct_orgs': ['departement-de-gestion-financiere',
                  'comptabilite',
                  'budget-et-plan-de-gestion',
                  'entites-consolidees',
                  'entites-consolidees-fabriques-deglises',
                  'recettes-ordinaires',
                  'depenses-ordinaires',
                  'recettes-et-depenses-extraordinaires',
                  'caisse-centrale',
                  'contentieux',
                  'dgf-observateurs',
                  'tutelle',
                  'redevances',
                  'taxes'], 'enabled': True},
]
