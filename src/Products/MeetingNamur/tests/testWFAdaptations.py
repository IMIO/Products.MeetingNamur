# -*- coding: utf-8 -*-
#
# File: testWFAdaptations.py
#
# Copyright (c) 2013 by Imio.be
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

from datetime import datetime
from Products.CMFCore.permissions import DeleteObjects
from Products.MeetingCommunes.tests.testWFAdaptations import testWFAdaptations as mctwfa
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase
from Products.PloneMeeting.tests.PloneMeetingTestCase import pm_logger


class testWFAdaptations(MeetingNamurTestCase, mctwfa):
    '''Tests various aspects of votes management.'''

    def test_pm_WFA_availableWFAdaptations(self):
        '''Most of wfAdaptations makes no sense, just make sure most are disabled.'''
        self.assertEquals(set(self.meetingConfig.listWorkflowAdaptations()),
                          {'item_validation_shortcuts',
                           'item_validation_no_validate_shortcuts',
                           'only_creator_may_delete',
                           'no_freeze',
                           'no_publication',
                           'no_decide',
                           'accepted_but_modified',
                           'postpone_next_meeting',
                           'mark_not_applicable',
                           'removed',
                           'removed_and_duplicated',
                           'refused',
                           'delayed',
                           'pre_accepted',
                           'reviewers_take_back_validated_item',
                           'presented_item_back_to_itemcreated',
                           'presented_item_back_to_proposed',
                           'return_to_proposing_group',
                           'return_to_proposing_group_with_last_validation',
                           'return_to_proposing_group_with_all_validations',
                           'accepted_out_of_meeting',
                           'accepted_out_of_meeting_and_duplicated',
                           'accepted_out_of_meeting_emergency',
                           'accepted_out_of_meeting_emergency_and_duplicated',
                           'transfered',
                           'transfered_and_duplicated',
                           'meetingmanager_correct_closed_meeting',
                           'namur_meetingmanager_may_not_edit_decision_project'
                           })

    def test_pm_Validate_workflowAdaptations_dependencies(self):
        '''Not all WFA are available yet...'''
        pass



def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testWFAdaptations, prefix='test_pm_'))
    return suite
