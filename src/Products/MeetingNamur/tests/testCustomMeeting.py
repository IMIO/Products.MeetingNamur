# -*- coding: utf-8 -*-
#
# File: testCustomMeeting.py
#
# Copyright (c) 2007-2012 by CommunesPlone.org
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


class testCustomMeeting(MeetingNamurTestCase):
    """
        Tests the Meeting adapted methods
    """

    def test_GetPrintableItemsByCategoryWithMeetingCategory(self):
        """
            This method aimed to ease printings should return a list of items ordered by category
        """
        #a list of lists where inner lists contain
        #a categrory (MeetingCategory or MeetingGroup) as first element and items of this category

        #configure PloneMeeting
        #test if the category is a MeetingCategory
        #insert items in the meeting depending on the category
        self.changeUser('admin')
        self.meetingConfig.setUseGroupsAsCategories(False)
        self.meetingConfig.insertingMethodsOnAddItem = ({'insertingMethod': 'on_categories', 'reverse': '0'}, )
        self._removeConfigObjectsFor(self.meetingConfig)
        #add a Meeting and present several items in different categories
        self.changeUser('pmManager')
        m = self.create('Meeting', date='2007/12/11 09:00:00')
        i1 = self.create('MeetingItem', title='Item1')
        i1.setProposingGroup('developers')
        i1.setCategory('deployment')
        i2 = self.create('MeetingItem', title='Item2')
        i2.setProposingGroup('developers')
        i2.setCategory('deployment')
        i3 = self.create('MeetingItem', title='Item3')
        i3.setProposingGroup('developers')
        i3.setCategory('deployment')
        i4 = self.create('MeetingItem', title='Item4')
        i4.setProposingGroup('developers')
        i4.setCategory('research')
        i5 = self.create('MeetingItem', title='Item5')
        i5.setProposingGroup('developers')
        i5.setCategory('research')
        i6 = self.create('MeetingItem', title='Item6')
        i6.setProposingGroup('developers')
        i6.setCategory('projects')
        i7 = self.create('MeetingItem', title='Item7')
        i7.setProposingGroup('developers')
        i7.setCategory('projects')
        items = (i1, i2, i3, i4, i5, i6, i7)
        #present every items in a meeting
        for item in items:
            self.do(item, 'propose')
            self.do(item, 'validate')
            self.do(item, 'present')
        #build the list of uids
        itemUids = []
        for item in m.getItemsInOrder():
            itemUids.append(item.UID())
        #test on the meeting
        #we should have a list containing 3 lists, 1 list by category
        self.assertEquals(len(m.adapted().getPrintableItemsByCategory(itemUids)), 3)
        #the order and the type should be kept, the first element of inner list is a MeetingCategory
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[0][0].getId(), 'deployment')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[1][0].getId(), 'research')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[2][0].getId(), 'projects')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[0][0].meta_type, 'MeetingCategory')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[1][0].meta_type, 'MeetingCategory')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[2][0].meta_type, 'MeetingCategory')
        #other element of the list are MeetingItems...
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[0][1].meta_type, 'MeetingItem')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[0][2].meta_type, 'MeetingItem')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[0][3].meta_type, 'MeetingItem')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[1][1].meta_type, 'MeetingItem')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[1][2].meta_type, 'MeetingItem')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[2][1].meta_type, 'MeetingItem')

    def test_GetPrintableItemsByCategoryWithMeetingGroup(self):
        """
            This method aimed to ease printings should return a list of items ordered by category
        """
        #a list of lists where inner lists contain
        #a categrory (MeetingCategory or MeetingGroup) as first element and items of this category

        #configure PloneMeeting
        #test if the category is a MeetingCategory
        #insert items in the meeting depending on the category
        self.changeUser('admin')
        self.meetingConfig.setUseGroupsAsCategories(True)
        self.meetingConfig.insertingMethodsOnAddItem = ({'insertingMethod': 'on_proposing_groups', 'reverse': '0'}, )
        self._removeConfigObjectsFor(self.meetingConfig)
        #add a Meeting and present several items in different categories
        self.changeUser('pmManager')
        m = self.create('Meeting', date='2007/12/11 09:00:00')
        i1 = self.create('MeetingItem', title='Item1')
        i1.setProposingGroup('developers')
        i2 = self.create('MeetingItem', title='Item2')
        i2.setProposingGroup('developers')
        i3 = self.create('MeetingItem', title='Item3')
        i3.setProposingGroup('developers')
        i4 = self.create('MeetingItem', title='Item4')
        i4.setProposingGroup('vendors')
        i5 = self.create('MeetingItem', title='Item5')
        i5.setProposingGroup('vendors')
        i6 = self.create('MeetingItem', title='Item6')
        i6.setProposingGroup('vendors')
        i7 = self.create('MeetingItem', title='Item7')
        i7.setProposingGroup('vendors')
        items = (i1, i2, i3, i4, i5, i6, i7)
        #present every items in a meeting
        for item in items:
            self.do(item, 'propose')
            self.do(item, 'validate')
            self.do(item, 'present')
        #build the list of uids
        itemUids = []
        for item in m.getItemsInOrder():
            itemUids.append(item.UID())
        #test on the meeting
        #we should have a list containing 3 lists, 1 list by category
        self.assertEquals(len(m.adapted().getPrintableItemsByCategory(itemUids)), 2)
        #the order and the type should be kept, the first element of inner list is a MeetingCategory
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[0][0].getId(), 'developers')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[1][0].getId(), 'vendors')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[0][0].meta_type, 'MeetingGroup')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[1][0].meta_type, 'MeetingGroup')
        #other element of the list are MeetingItems...
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[0][1].meta_type, 'MeetingItem')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[0][2].meta_type, 'MeetingItem')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[0][3].meta_type, 'MeetingItem')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[1][1].meta_type, 'MeetingItem')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[1][2].meta_type, 'MeetingItem')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[1][3].meta_type, 'MeetingItem')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[1][4].meta_type, 'MeetingItem')

    def test_InitializeDecisionField(self):
        """
            In the doDecide method, we initialize the Decision field to a default value made of
            Title+Description if the field is empty...
        """
        #check that it works
        #check that if the field contains something, it is not intialized again
        self.changeUser('admin')
        self._removeConfigObjectsFor(self.meetingConfig)
        self.changeUser('pmManager')
        m = self.create('Meeting', date='2007/12/11 09:00:00')
        #create some items
        #empty decision
        i1 = self.create('MeetingItem', title='Item1')
        i1.setDecision("")
        i1.setDescription("<p>Description Item1</p>")
        i1.setProposingGroup('developers')
        #decision field is already filled
        i2 = self.create('MeetingItem', title='Item2')
        i2.setDecision("<p>Decision Item2</p>")
        i2.setDescription("<p>Description Item2</p>")
        i2.setProposingGroup('developers')
        #create an item with the default Kupu empty value
        i3 = self.create('MeetingItem', title='Item3')
        i3.setDecision("<p></p>")
        i3.setDescription("<p>Description Item3</p>")
        i3.setProposingGroup('developers')
        #present every items in the meeting
        items = (i1, i2, i3)
        #check the decision field of every item
        self.assertEquals(i1.getDecision(), "")
        self.assertEquals(i2.getDecision(), "<p>Decision Item2</p>")
        self.assertEquals(i3.getDecision(), "<p></p>")
        for item in items:
            self.do(item, 'propose')
            self.do(item, 'validate')
            self.do(item, 'present')
        #now the decision field initialization has occured
        #i1 should be initialized
        self.assertEquals(i1.getDecision(), "<p>Description Item1</p>")
        #i2 sould not have changed
        self.assertEquals(i2.getDecision(), "<p>Decision Item2</p>")
        #i3 is initlaized because the decision field contained an empty_value
        self.assertEquals(i3.getDecision(), "<p>Description Item3</p>")
        #decide the meeting (freez it before ;-))
        self.do(m, 'freeze')
        self.do(m, 'decide')
        #now that the meeting is decided, the decision field not change
        #i1 should be initialized
        self.assertEquals(i1.getDecision(), "<p>Description Item1</p>")
        #i2 sould not have changed
        self.assertEquals(i2.getDecision(), "<p>Decision Item2</p>")
        #i3 is initlaized because the decision field contained an empty_value
        self.assertEquals(i3.getDecision(), "<p>Description Item3</p>")
