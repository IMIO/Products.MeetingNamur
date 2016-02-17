# -*- coding: utf-8 -*-
#
# File: testMeetingItem.py
#
# Copyright (c) 2007 by PloneGov
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

from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase
from Products.MeetingCommunes.tests.testMeetingItem import testMeetingItem as mctmi
from Products.statusmessages.interfaces import IStatusMessage
from Products.PloneMeeting.utils import ON_TRANSITION_TRANSFORM_TAL_EXPR_ERROR


class testMeetingItem(MeetingNamurTestCase, mctmi):
    """
        Tests the MeetingItem class methods.
    """

    def test_subproduct_call_PowerObserversLocalRoles(self):
        '''See doc string in PloneMeeting.'''
        self.test_pm_PowerObserversLocalRoles()

    def test_subproduct_call_OnTransitionFieldTransforms(self):
        ''' We must ovveride this test because for Namur, the decision field is never fill by creator or reviewer
           On transition triggered, some transforms can be applied to item or meeting
           rich text field depending on what is defined in MeetingConfig.onTransitionFieldTransforms.
           This is used for example to adapt the text of the decision when an item is delayed or refused.
           '''
        self.changeUser('pmManager')
        meeting = self._createMeetingWithItems()
        self.decideMeeting(meeting)
        # we will adapt item decision when the item is delayed
        item1 = meeting.getItems()[0]
        originalDecision = '<p>Current item decision.</p>'
        item1.setDecision(originalDecision)
        # for now, as nothing is defined, nothing happens when item is delayed
        self.do(item1, 'delay')
        self.assertTrue(item1.getDecision(keepWithNext=False) == originalDecision)
        # configure onTransitionFieldTransforms and delay another item
        delayedItemDecision = '<p>This item has been delayed.</p>'
        self.meetingConfig.setOnTransitionFieldTransforms(
            ({'transition': 'delay',
              'field_name': 'MeetingItem.decision',
              'tal_expression': 'string:%s' % delayedItemDecision},))
        item2 = meeting.getItems()[1]
        item2.setDecision(originalDecision)
        self.do(item2, 'delay')
        self.assertTrue(item2.getDecision(keepWithNext=False) == delayedItemDecision)
        # if the item was duplicated (often the case when delaying an item), the duplicated
        # item keep the original decision
        duplicatedItem = item2.getBRefs('ItemPredecessor')[0]
        # right duplicated item
        self.assertTrue(duplicatedItem.getPredecessor() == item2)
        self.assertTrue(duplicatedItem.getDecision(keepWithNext=False) == '<p>&nbsp;</p>')
        # this work also when triggering any other item or meeting transition with every rich fields
        item3 = meeting.getItems()[2]
        self.meetingConfig.setOnTransitionFieldTransforms(
            ({'transition': 'accept',
              'field_name': 'MeetingItem.description',
              'tal_expression': 'string:<p>My new description.</p>'},))
        item3.setDescription('<p>My original description.</p>')
        self.do(item3, 'accept')
        self.assertTrue(item3.Description() == '<p>My new description.</p>')
        # if ever an error occurs with the TAL expression, the transition
        # is made but the rich text is not changed and a portal_message is displayed
        self.meetingConfig.setOnTransitionFieldTransforms(
            ({'transition': 'accept',
              'field_name': 'MeetingItem.decision',
              'tal_expression': 'some_wrong_tal_expression'},))
        item4 = meeting.getItems()[3]
        item4.setDecision('<p>My decision that will not be touched.</p>')
        self.do(item4, 'accept')
        # transition was triggered
        self.assertTrue(item4.queryState() == 'accepted')
        # original decision was not touched
        self.assertTrue(item4.getDecision(keepWithNext=False) == '<p>My decision that will not be touched.</p>')
        # a portal_message is displayed to the user that triggered the transition
        messages = IStatusMessage(self.request).show()
        self.assertTrue(messages[0].message == ON_TRANSITION_TRANSFORM_TAL_EXPR_ERROR % ('decision',
                                                                                         "'some_wrong_tal_expression'"))

    def test_subproduct_call_ItemStrikedAssembly(self):
        self.test_pm_ItemStrikedAssembly()

    def test_subproduct_call_Emergency(self):
        self.test_pm_Emergency()

    def test_subproduct_call_Completeness(self):
        self.test_pm_Completeness()

    def test_subproduct_call_SendItemToOtherMCManually(self):
        self.test_pm_SendItemToOtherMCManually()


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    # launch only tests prefixed by 'test_mc_' to avoid launching the tests coming from mctmi
    suite.addTest(makeSuite(testMeetingItem, prefix='test_subproduct_'))
    return suite
