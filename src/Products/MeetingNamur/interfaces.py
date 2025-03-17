# -*- coding: utf-8 -*-
#
# GNU General Public License (GPL)
#

__author__ = """Andre Nuyens <a.nuyens@imio.be>"""
__docformat__ = 'plaintext'

from Products.MeetingCommunes.interfaces import IMeetingCommunesLayer
from Products.PloneMeeting.interfaces import IMeetingItemWorkflowActions
from Products.PloneMeeting.interfaces import IMeetingItemWorkflowConditions
from Products.PloneMeeting.interfaces import IMeetingWorkflowActions
from Products.PloneMeeting.interfaces import IMeetingWorkflowConditions


class IMeetingItemNamurWorkflowActions(IMeetingItemWorkflowActions):
    '''This interface represents a meeting item as viewed by the specific
       item workflow that is defined in this MeetingNamur product.'''
    def doPresent():
        """
          Triggered while doing the 'present' transition
        """
    def doAcceptButModify():
        """
          Triggered while doing the 'accept_but_modify' transition
        """
    def doPreAccept():
        """
          Triggered while doing the 'pre_accept' transition
        """


class IMeetingItemNamurCollegeWorkflowActions(IMeetingItemNamurWorkflowActions):
    '''inherit class'''


class IMeetingItemNamurCouncilWorkflowActions(IMeetingItemNamurWorkflowActions):
    '''inherit class'''


class IMeetingItemNamurWorkflowConditions(IMeetingItemWorkflowConditions):
    '''This interface represents a meeting item as viewed by the specific
       item workflow that is defined in this MeetingNamur product.'''
    def mayDecide():
        """
          Guard for the 'decide' transition
        """
    def isLateFor():
        """
          is the MeetingItem considered as late
        """
    def mayFreeze():
        """
          Guard for the 'freeze' transition
        """


class IMeetingItemNamurCollegeWorkflowConditions(IMeetingItemNamurWorkflowConditions):
    '''inherit class'''


class IMeetingItemNamurCouncilWorkflowConditions(IMeetingItemNamurWorkflowConditions):
    '''inherit class'''


class IMeetingNamurWorkflowActions(IMeetingWorkflowActions):
    '''inherit class'''


class IMeetingNamurCollegeWorkflowActions(IMeetingNamurWorkflowActions):
    '''inherit class'''


class IMeetingNamurCouncilWorkflowActions(IMeetingNamurWorkflowActions):
    '''inherit class'''


class IMeetingNamurWorkflowConditions(IMeetingWorkflowConditions):
    '''This interface represents a meeting as viewed by the specific meeting
       workflow that is defined in this MeetingNamur product.'''
    def mayFreeze():
        """
          Guard for the 'freeze' transition
        """
    def mayClose():
        """
          Guard for the 'close' transitions
        """
    def mayDecide():
        """
          Guard for the 'decide' transition
        """
    def mayChangeItemsOrder():
        """
          Check if the user may or not changes the order of the items on the meeting
        """


class IMeetingNamurCollegeWorkflowConditions(IMeetingNamurWorkflowConditions):
    '''inherit class'''


class IMeetingNamurCouncilWorkflowConditions(IMeetingNamurWorkflowConditions):
    '''inherit class'''


class IMeetingNamurLayer(IMeetingCommunesLayer):
    ''' '''
