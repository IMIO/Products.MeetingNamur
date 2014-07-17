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

from Products.MeetingNamur.tests.MeetingNamurTestCase import \
    MeetingNamurTestCase

class testMeetingGroup(MeetingNamurTestCase):
    '''Tests the MeetingGroup adapted methods.'''

    def testListEchevinServices(self):
        self.changeUser('admin')
        from Products.Archetypes.atapi import DisplayList
        les = DisplayList([('developers', u'Developers'), ('vendors', u'Vendors'), ('finances', u'Finances'), ('taxes', u'Taxes')])
        meetingGroups = self.tool.objectValues('MeetingGroup')
        self.assertEquals(meetingGroups[0].listEchevinServices(),les)

    def testOnEdit(self):
        '''Add group_budgetimpactreviewers if DGF group'''
        self.changeUser('admin')
        #acronym of finance group is DGF, we must have budgetimpactreviewers groupe (in users and group)
        self.failUnless(self.tool.portal_groups.getGroupById('finances_budgetimpactreviewers'))
        #acronym of vendors group is devil, we must not have budgetimpactreviewers groupe (in users and group)
        self.failIf(self.tool.portal_groups.getGroupById('vendors_budgetimpactreviewers'))
