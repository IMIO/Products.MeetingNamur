# -*- coding: utf-8 -*-

from Products.MeetingCommunes.tests.testCustomMeetingItem import testCustomMeetingItem as mctcmi
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase


class testCustomMeeting(MeetingNamurTestCase, mctcmi):
    """
        Tests the Meeting adapted methods
    """

    def test_GetPrintableItemsByCategoryWithMeetingCategory(self):
        """
            This method aimed to ease printings should return a list of items ordered by category
        """
        # a list of lists where inner lists contain
        # a categrory (MeetingCategory or MeetingGroup) as first element and items of this category

        # configure PloneMeeting
        # test if the category is a MeetingCategory
        # insert items in the meeting depending on the category
        self.changeUser('pmManager')
        self.setMeetingConfig(self.meetingConfig2.getId())
        meeting = self._createMeetingWithItems()
        i6 = self.create('MeetingItem', title='Item6')
        i6.setCategory('development')
        i7 = self.create('MeetingItem', title='Item7')
        i7.setCategory('development')
        self.presentItem(i6)
        self.presentItem(i7)
        # build the list of uids
        itemUids = [anItem.UID() for anItem in meeting.getItems(ordered=True)]
        # the 2 new development items are moved to the end of the meeting
        view = i6.restrictedTraverse('@@change-item-order')
        view('number', '7')
        view('down')
        view = i7.restrictedTraverse('@@change-item-order')
        view('number', '7')
        # test on the meeting
        # we should have a list containing 3 lists, 1 list by category

        self.assertEquals(len(meeting.adapted().getPrintableItemsByCategory(itemUids)), 3)
        # the order and the type should be kept, the first element of inner list is a MeetingCategory
        self.assertEquals(meeting.adapted().getPrintableItemsByCategory(itemUids)[0][0].getId(), 'development')
        self.assertEquals(meeting.adapted().getPrintableItemsByCategory(itemUids)[1][0].getId(), 'events')
        self.assertEquals(meeting.adapted().getPrintableItemsByCategory(itemUids)[2][0].getId(), 'research')
        self.assertEquals(meeting.adapted().getPrintableItemsByCategory(itemUids)[0][0].portal_type, 'meetingcategory')
        self.assertEquals(meeting.adapted().getPrintableItemsByCategory(itemUids)[1][0].portal_type, 'meetingcategory')
        self.assertEquals(meeting.adapted().getPrintableItemsByCategory(itemUids)[2][0].portal_type, 'meetingcategory')
        # the first category should have 4 items, the second 2 and the third 1 ( + 1 category element for each one)
        self.assertEquals(len(meeting.adapted().getPrintableItemsByCategory(itemUids)[0]), 5)
        self.assertEquals(len(meeting.adapted().getPrintableItemsByCategory(itemUids)[1]), 3)
        self.assertEquals(len(meeting.adapted().getPrintableItemsByCategory(itemUids)[2]), 2)
        # other element of the list are MeetingItems...
        self.assertEquals(meeting.adapted().getPrintableItemsByCategory(itemUids)[0][1].meta_type, 'MeetingItem')
        self.assertEquals(meeting.adapted().getPrintableItemsByCategory(itemUids)[0][2].meta_type, 'MeetingItem')
        self.assertEquals(meeting.adapted().getPrintableItemsByCategory(itemUids)[0][3].meta_type, 'MeetingItem')
        self.assertEquals(meeting.adapted().getPrintableItemsByCategory(itemUids)[0][4].meta_type, 'MeetingItem')
        self.assertEquals(meeting.adapted().getPrintableItemsByCategory(itemUids)[1][1].meta_type, 'MeetingItem')
        self.assertEquals(meeting.adapted().getPrintableItemsByCategory(itemUids)[1][2].meta_type, 'MeetingItem')
        self.assertEquals(meeting.adapted().getPrintableItemsByCategory(itemUids)[2][1].meta_type, 'MeetingItem')

    def test_GetPrintableItemsByCategoryWithMeetingGroup(self):
        """
            This method aimed to ease printings should return a list of items ordered by category
        """
        # a list of lists where inner lists contain
        # a categrory (MeetingCategory or MeetingGroup) as first element and items of this category

        # configure PloneMeeting
        # test if the category is a MeetingCategory
        # insert items in the meeting depending on the category
        self.changeUser('admin')
        self.meetingConfig.setUseGroupsAsCategories(True)
        self.meetingConfig.insertingMethodsOnAddItem = ({'insertingMethod': 'on_proposing_groups', 'reverse': '0'}, )
        self._removeConfigObjectsFor(self.meetingConfig)
        # add a Meeting and present several items in different categories
        self.changeUser('pmManager')
        m = self.create('Meeting', date='2007/12/11 09:00:00')
        i1 = self.create('MeetingItem', title='Item1')
        i1.setProposingGroup(self.developers_uid)
        i2 = self.create('MeetingItem', title='Item2')
        i2.setProposingGroup(self.developers_uid)
        i3 = self.create('MeetingItem', title='Item3')
        i3.setProposingGroup(self.developers_uid)
        i4 = self.create('MeetingItem', title='Item4')
        i4.setProposingGroup(self.vendors_uid)
        i5 = self.create('MeetingItem', title='Item5')
        i5.setProposingGroup(self.vendors_uid)
        i6 = self.create('MeetingItem', title='Item6')
        i6.setProposingGroup(self.vendors_uid)
        i7 = self.create('MeetingItem', title='Item7')
        i7.setProposingGroup(self.vendors_uid)
        items = (i1, i2, i3, i4, i5, i6, i7)
        # present every items in a meeting
        self.changeUser('admin')
        for item in items:
            self.presentItem(item)
        self.changeUser('pmManager')

        # build the list of uids
        itemUids = []
        for item in m.getItemsInOrder():
            itemUids.append(item.UID())
        # test on the meeting
        # we should have a list containing 3 lists, 1 list by category
        self.assertEquals(len(m.adapted().getPrintableItemsByCategory(itemUids)), 2)
        self.assertEquals(len(m.adapted().getPrintableItemsByCategory(itemUids, includeEmptyCategories=True)), 2)
        # the order and the type should be kept, the first element of inner list is a MeetingCategory
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[0][0].getId(), 'developers')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[1][0].getId(), 'vendors')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[0][0].portal_type, 'organization')
        self.assertEquals(m.adapted().getPrintableItemsByCategory(itemUids)[1][0].portal_type, 'organization')
        # other element of the list are MeetingItems...
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
        # check that it works
        # check that if the field contains something, it is not intialized again
        self.changeUser('admin')
        self._removeConfigObjectsFor(self.meetingConfig)
        self.changeUser('pmManager')
        m = self.create('Meeting', date='2007/12/11 09:00:00')
        # create some items
        # empty decision
        i1 = self.create('MeetingItem', title='Item1')
        i1.setDecision("")
        i1.setDescription("<p>Description Item1</p>")
        i1.setProposingGroup(self.developers_uid)
        # decision field is already filled
        i2 = self.create('MeetingItem', title='Item2')
        i2.setDecision("<p>Decision Item2</p>")
        i2.setDescription("<p>Description Item2</p>")
        i2.setProposingGroup(self.developers_uid)
        # create an item with the default Kupu empty value
        i3 = self.create('MeetingItem', title='Item3')
        i3.setDecision("<p></p>")
        i3.setDescription("<p>Description Item3</p>")
        i3.setProposingGroup(self.developers_uid)
        # present every items in the meeting
        items = (i1, i2, i3)
        # check the decision field of every item
        self.assertEquals(i1.getDecision(), "")
        self.assertEquals(i2.getDecision(), "<p>Decision Item2</p>")
        self.assertEquals(i3.getDecision(), "<p></p>")
        for item in items:
            self.do(item, 'propose')
            self.do(item, 'validate')
            self.do(item, 'present')
        # now the decision field initialization has occured
        # i1 should be initialized
        self.assertEquals(i1.getDecision(), "<p>Description Item1</p>")
        # i2 sould not have changed
        self.assertEquals(i2.getDecision(), "<p>Decision Item2</p>")
        # i3 is initlaized because the decision field contained an empty_value
        self.assertEquals(i3.getDecision(), "<p>Description Item3</p>")
        # decide the meeting (freez it before ;-))
        self.do(m, 'freeze')
        self.do(m, 'decide')
        # now that the meeting is decided, the decision field not change
        # i1 should be initialized
        self.assertEquals(i1.getDecision(), "<p>Description Item1</p>")
        # i2 sould not have changed
        self.assertEquals(i2.getDecision(), "<p>Decision Item2</p>")
        # i3 is initlaized because the decision field contained an empty_value
        self.assertEquals(i3.getDecision(), "<p>Description Item3</p>")


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testCustomMeeting, prefix='test_'))
    return suite
