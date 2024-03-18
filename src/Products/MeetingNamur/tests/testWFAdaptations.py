# -*- coding: utf-8 -*-
#
# GNU General Public License (GPL)
#

from imio.helpers.content import get_vocab_values
from Products.MeetingCommunes.tests.testWFAdaptations import testWFAdaptations as mctwfa
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase
from Products.PloneMeeting.config import MEETING_REMOVE_MOG_WFA


class testWFAdaptations(MeetingNamurTestCase, mctwfa):
    '''Tests various aspects of votes management.'''

    def test_pm_WFA_availableWFAdaptations(self):
        '''Most of wfAdaptations makes no sense, just make sure most are disabled.'''
        self.assertEqual(
            sorted(get_vocab_values(self.meetingConfig, 'WorkflowAdaptations')),
            ['accepted_but_modified',
             'accepted_out_of_meeting',
             'accepted_out_of_meeting_and_duplicated',
             'accepted_out_of_meeting_emergency',
             'accepted_out_of_meeting_emergency_and_duplicated',
             'delayed',
             'item_validation_no_validate_shortcuts',
             'item_validation_shortcuts',
             'mark_not_applicable',
             MEETING_REMOVE_MOG_WFA,
             'meetingmanager_correct_closed_meeting',
             # custom WFA
             'namur_meetingmanager_may_not_edit_decision_project',
             'no_decide',
             'no_freeze',
             'no_publication',
             'only_creator_may_delete',
             'postpone_next_meeting',
             'pre_accepted',
             'presented_item_back_to_itemcreated',
             'presented_item_back_to_proposed',
             'refused',
             'removed',
             'removed_and_duplicated',
             'return_to_proposing_group',
             'return_to_proposing_group_with_all_validations',
             'return_to_proposing_group_with_last_validation',
             'reviewers_take_back_validated_item',
             'transfered',
             'transfered_and_duplicated']
        )

    def test_pm_Validate_workflowAdaptations_dependencies(self):
        '''Not all WFA are available yet...'''
        pass


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testWFAdaptations, prefix='test_pm_'))
    return suite
