# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Copyright (c) 2007 by Imio
#
# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#

__author__ = """Andre Nuyens <a.nuyens@imio.be>"""
__docformat__ = 'plaintext'

# ------------------------------------------------------------------------------
from Products.PloneMeeting.interfaces import IMeetingItemWorkflowActions
from Products.PloneMeeting.interfaces import IMeetingItemWorkflowConditions
from Products.PloneMeeting.interfaces import IMeetingWorkflowActions
from Products.PloneMeeting.interfaces import IMeetingWorkflowConditions


# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------
