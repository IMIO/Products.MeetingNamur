# -*- coding: utf-8 -*-
#
# File: testMeetingGroup.py
#
# Copyright (c) 2007-2013 by Imio.be
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

from plone.app.testing import logout
from Products.MeetingCommunes.tests.MeetingCommunesTestCase import \
    MeetingCommunesTestCase
from Products.PloneMeeting.tests.testMeetingGroup import testMeetingGroup as pmmg


class testMeetingGroup(MeetingCommunesTestCase, pmmg):
    '''Tests the testMeetingGroup class methods.'''

    def test_subproduct_call_CanNotRemoveUsedMeetingGroup(self):
        '''Run the testCanNotRemoveUsedMeetingCategory from PloneMeeting.'''
        # remove every recurring items in existing meetingConfigs except template2 in self.meetingConfig
        self.changeUser('admin')
        self.meetingConfig.recurringitems.manage_delObjects(
            [item.getId() for item in (self.meetingConfig.getItems() +
                                       [self.meetingConfig.recurringitems.template1, ])])
        self.meetingConfig2.recurringitems.manage_delObjects(
            [item.getId() for item in (self.meetingConfig2.recurringitems.objectValues('MeetingItem'))])
        logout()
        self.test_pm_CanNotRemoveUsedMeetingGroup()


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testMeetingGroup, prefix='test_subproduct_'))
    return suite
