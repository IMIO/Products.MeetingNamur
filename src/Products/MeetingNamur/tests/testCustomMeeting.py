# -*- coding: utf-8 -*-
from DateTime import DateTime
from Products.MeetingCommunes.tests.testCustomMeetingItem import testCustomMeetingItem as mctcmi
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase


class testCustomMeeting(MeetingNamurTestCase, mctcmi):
    """
        Tests the Meeting adapted methods
    """

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
        m = self.create('Meeting', date=DateTime('2007/12/11 09:00:00').asdatetime())
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
        self.decideMeeting(m)
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
