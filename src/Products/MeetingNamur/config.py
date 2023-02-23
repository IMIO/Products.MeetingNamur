# -*- coding: utf-8 -*-

from Products.CMFCore.permissions import setDefaultRoles
from Products.PloneMeeting import config as PMconfig


PROJECTNAME = "MeetingNamur"

# Permissions
WriteDecisionProject = 'MeetingNamur: Write decisionProject'
setDefaultRoles(WriteDecisionProject, ('Manager', 'Member'))
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
                  'taxes'],
     "fct_management": False,
     'enabled': True
     },
]

NAMUR_ITEM_WF_VALIDATION_LEVELS = (
    {'state': 'itemcreated',
     'state_title': 'itemcreated',
     'leading_transition': '-',
     'leading_transition_title': '-',
     'back_transition': 'backToItemCreated',
     'back_transition_title': 'backToItemCreated',
     'suffix': 'creators',
     # only creators may manage itemcreated item
     'extra_suffixes': [],
     'enabled': '1',
     },
    {'state': 'proposed_to_servicehead',
     'state_title': 'proposed_to_servicehead',
     'leading_transition': 'proposeToServiceHead',
     'leading_transition_title': 'proposeToServiceHead',
     'back_transition': 'backToProposedToServiceHead',
     'back_transition_title': 'backToProposedToServiceHead',
     'suffix': 'serviceheads',
     'extra_suffixes': [],
     'enabled': '1',
     },
    {'state': 'proposed_to_officemanager',
     'state_title': 'proposed_to_officemanager',
     'leading_transition': 'proposeToOfficeManager',
     'leading_transition_title': 'proposeToOfficeManager',
     'back_transition': 'backToProposedToOfficeManager',
     'back_transition_title': 'backToProposedToOfficeManager',
     'suffix': 'officemanagers',
     'enabled': '1',
     'extra_suffixes': [],
     },
    {'state': 'proposed_to_divisionhead',
     'state_title': 'proposed_to_divisionhead',
     'leading_transition': 'proposeToDivisionHead',
     'leading_transition_title': 'proposeToDivisionHead',
     'back_transition': 'backToProposedToDivisionHead',
     'back_transition_title': 'backToProposedToDivisionHead',
     'suffix': 'divisionheads',
     'enabled': '1',
     'extra_suffixes': [],
     },
    {'state': 'proposed',
     'state_title': 'proposed',
     'leading_transition': 'propose',
     'leading_transition_title': 'propose',
     'back_transition': 'backToProposed',
     'back_transition_title': 'backToProposed',
     'suffix': 'reviewers',
     'extra_suffixes': [],
     'enabled': '1',
     },
)
