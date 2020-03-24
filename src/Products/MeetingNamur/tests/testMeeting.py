# -*- coding: utf-8 -*-
#
# File: testMeeting.py
#
# Copyright (c) 2007-2010 by PloneGov
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
from Products.MeetingCommunes.tests.testMeeting import testMeeting as mctm


class testMeeting(MeetingNamurTestCase, mctm):
    """
        Tests the Meeting class methods.
    """

    def test_pm_RemoveOrDeleteLinkedItem(self):
        """
            Give temporary manager right to pmManager.
        """
        self.portal.acl_users.portal_role_manager.assignRoleToPrincipal('Manager', 'pmManager')
        mctm.test_pm_RemoveOrDeleteLinkedItem(self)


    def test_pm_MeetingNumbers(self):
        '''Tests that meetings receive correctly their numbers from the config
           when they are freezing.'''
        self.changeUser('pmManager')
        m1 = self._createMeetingWithItems()
        self.assertEquals(self.meetingConfig.getLastMeetingNumber(), 0)
        self.assertEquals(m1.getMeetingNumber(), -1)
        self.decideMeeting(m1)
        self.assertEquals(m1.getMeetingNumber(), 1)
        self.assertEquals(self.meetingConfig.getLastMeetingNumber(), 1)
        m2 = self._createMeetingWithItems()
        self.decideMeeting(m2)
        self.assertEquals(m2.getMeetingNumber(), 2)
        self.assertEquals(self.meetingConfig.getLastMeetingNumber(), 2)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testMeeting, prefix='test_pm_'))
    return suite
