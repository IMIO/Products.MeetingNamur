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

from DateTime import DateTime
from Products.CMFCore.permissions import DeleteObjects
from Products.MeetingCommunes.tests.testWFAdaptations import testWFAdaptations as mctwfa
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase
from Products.PloneMeeting.model.adaptations import RETURN_TO_PROPOSING_GROUP_CUSTOM_PERMISSIONS
from Products.PloneMeeting.model.adaptations import RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE
from Products.PloneMeeting.model.adaptations import RETURN_TO_PROPOSING_GROUP_VALIDATION_STATES


class testWFAdaptations(MeetingNamurTestCase, mctwfa):
    '''Tests various aspects of votes management.'''

    def test_pm_WFA_availableWFAdaptations(self):
        '''Most of wfAdaptations makes no sense, just make sure most are disabled.'''
        self.assertEquals(set(self.meetingConfig.listWorkflowAdaptations()),
                          {'return_to_proposing_group',
                               'return_to_proposing_group_with_last_validation',
                               'return_to_proposing_group_with_all_validations'})

    def test_pm_WFA_no_publication(self):
        '''No sense...'''
        pass

    def test_pm_WFA_no_proposal(self):
        '''No sense...'''
        pass

    def test_pm_WFA_pre_validation(self):
        '''No sense...'''
        pass

    def test_pm_WFA_items_come_validated(self):
        '''No sense...'''
        pass

    def test_pm_WFA_only_creator_may_delete(self):
        '''No sense...'''
        pass

    def test_pm_WFA_no_global_observation(self):
        '''No sense...'''
        pass

    def test_pm_WFA_everyone_reads_all(self):
        '''No sense...'''
        pass

    def test_pm_WFA_creator_edits_unless_closed(self):
        '''No sense...'''
        pass

    def test_pm_WFA_add_published_state(self):
        '''No sense...'''
        pass

    def test_pm_WFA_creator_initiated_decisions(self):
        '''No sense...'''
        pass

    def test_pm_WFA_local_meeting_managers(self):
        '''No sense...'''
        pass

    def test_pm_WFA_return_to_proposing_group_with_hide_decisions_when_under_writing(self):
        '''No sense...'''
        pass

    def test_pm_WFA_return_to_proposing_group_with_all_validations(self):
        '''Not used yet...'''
        pass

    def test_pm_WFA_return_to_proposing_group_with_last_validation(self):
        '''Not used yet...'''
        pass

    def _return_to_proposing_group_inactive(self):
        '''Tests while 'return_to_proposing_group' wfAdaptation is inactive.'''
        # this is active by default in MeetingCPASLalouviere council wf
        return

    def _return_to_proposing_group_active_state_to_clone(self):
        '''Helper method to test 'return_to_proposing_group' wfAdaptation regarding the
           RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE defined value.
           In our usecase, this is Nonsense as we use RETURN_TO_PROPOSING_GROUP_CUSTOM_PERMISSIONS.'''
        return

    def _return_to_proposing_group_active_custom_permissions(self):
        '''Helper method to test 'return_to_proposing_group' wfAdaptation regarding the
           RETURN_TO_PROPOSING_GROUP_CUSTOM_PERMISSIONS defined value.
           In our use case, just test that permissions of 'returned_to_proposing_group' state
           are the one defined in RETURN_TO_PROPOSING_GROUP_CUSTOM_PERMISSIONS.'''
        cfg = self.meetingConfig
        itemWF = self.wfTool.getWorkflowsFor(cfg.getItemTypeName())[0]
        returned_to_proposing_group_state_permissions = itemWF.states['returned_to_proposing_group'].permission_roles
        for permission in returned_to_proposing_group_state_permissions:
            self.assertEquals(returned_to_proposing_group_state_permissions[permission],
                              RETURN_TO_PROPOSING_GROUP_CUSTOM_PERMISSIONS[cfg.getItemWorkflow()][permission])

    def _return_to_proposing_group_active_wf_functionality(self):
        '''Tests the workflow functionality of using the 'return_to_proposing_group' wfAdaptation.
           Same as default test until the XXX here under.'''
        # while it is active, the creators of the item can edit the item as well as the MeetingManagers
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        self.proposeItem(item)
        self.changeUser('pmReviewer1')
        self.validateItem(item)
        # create a Meeting and add the item to it
        self.changeUser('pmManager')
        meeting = self.create('Meeting', date=DateTime())
        self.presentItem(item)
        # now that it is presented, the pmCreator1/pmReviewer1 can not edit it anymore
        for userId in ('pmCreator1', 'pmReviewer1'):
            self.changeUser(userId)
            self.failIf(self.hasPermission('Modify portal content', item))
        # the item can be send back to the proposing group by the MeetingManagers only
        for userId in ('pmCreator1', 'pmReviewer1'):
            self.changeUser(userId)
            self.failIf(self.wfTool.getTransitionsFor(item))
        self.changeUser('pmManager')
        self.failUnless('return_to_proposing_group' in [tr['name'] for tr in self.wfTool.getTransitionsFor(item)])
        # send the item back to the proposing group so the proposing group as an edit access to it
        self.do(item, 'return_to_proposing_group')
        self.changeUser('pmCreator1')
        self.failUnless(self.hasPermission('Modify portal content', item))
        # MeetingManagers can still edit it also
        self.changeUser('pmManager')
        self.failUnless(self.hasPermission('Modify portal content', item))
        # the creator can send the item back to the meeting managers, as the meeting managers
        for userId in ('pmCreator1', 'pmManager'):
            self.changeUser(userId)
            self.failUnless('backTo_presented_from_returned_to_proposing_group' in
                            [tr['name'] for tr in self.wfTool.getTransitionsFor(item)])
        # when the creator send the item back to the meeting, it is in the right state depending
        # on the meeting state.  Here, when meeting is 'created', the item is back to 'presented'
        self.do(item, 'backTo_presented_from_returned_to_proposing_group')
        self.assertEquals(item.queryState(), 'presented')
        # XXX changed by MeetingNamur
        # send the item back to proposing group, set the meeting in_committee then send the item back to the meeting
        # the item should be now in the item state corresponding to the meeting frozen state, so 'itemfrozen'
        self.do(item, 'return_to_proposing_group')
        self.do(meeting, 'freeze')


def _return_to_proposing_group_with_validation_active_state_to_clone(self):
    '''Helper method to test 'return_to_proposing_group' wfAdaptation regarding the
       RETURN_TO_PROPOSING_GROUP_VALIDATING_STATES defined value.'''
    # make sure permissions of the new state correspond to permissions of the state
    # defined in the model.adaptations.RETURN_TO_PROPOSING_GROUP_WITH_LAST_VALIDATION_STATE_TO_CLONE item state name
    # just take care that for new state, MeetingManager have been added to every permissions
    # this has only sense if using it, aka no RETURN_TO_PROPOSING_GROUP_WITH_LAST_VALIDATION_CUSTOM_PERMISSIONS
    # this could be the case if a subproduct (MeetingXXX) calls this test...
    itemWF = self.wfTool.getWorkflowsFor(self.meetingConfig.getItemTypeName())[0]
    cfgItemWFId = self.meetingConfig.getItemWorkflow()

    state_to_clone_ids = (RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE.get(cfgItemWFId).split('.')[1],) + \
        RETURN_TO_PROPOSING_GROUP_VALIDATION_STATES
    for state_to_clone_id in state_to_clone_ids:
        cloned_state_permissions = itemWF.states[state_to_clone_id].permission_roles
        returned_state = 'returned_to_proposing_group'
        if state_to_clone_id != 'itemcreated':
            returned_state += '_{0}'.format(state_to_clone_id)
        new_state_permissions = itemWF.states[returned_state].permission_roles
        for permission in cloned_state_permissions:
            cloned_state_permission_with_meetingmanager = []
            acquired = isinstance(cloned_state_permissions[permission], list) and True or False
            if 'MeetingManager' not in cloned_state_permissions[permission]:
                cloned_state_permission_with_meetingmanager = list(cloned_state_permissions[permission])
                cloned_state_permission_with_meetingmanager.append('MeetingManager')
            else:
                cloned_state_permission_with_meetingmanager = list(cloned_state_permissions[permission])

            # 'Delete objects' is only given to ['Manager', ]
            if permission == DeleteObjects:
                cloned_state_permission_with_meetingmanager = ['Manager', ]
            if not acquired:
                cloned_state_permission_with_meetingmanager = tuple(cloned_state_permission_with_meetingmanager)
            self.assertEquals(cloned_state_permission_with_meetingmanager,
                              new_state_permissions[permission])
            # Permission acquisition is also cloned
            self.assertEquals(
                itemWF.states[state_to_clone_id].getPermissionInfo(permission)['acquired'],
                itemWF.states[returned_state].getPermissionInfo(permission)['acquired'])


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testWFAdaptations, prefix='test_pm_'))
    return suite
