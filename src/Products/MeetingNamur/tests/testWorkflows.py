# -*- coding: utf-8 -*-
#
# File: testWorkflows.py
#
# GNU General Public License (GPL)
#

from AccessControl import Unauthorized
from DateTime import DateTime
from Products.MeetingCommunes.tests.testWorkflows import testWorkflows as mctw
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase
from Products.PloneMeeting.tests.PloneMeetingTestCase import pm_logger


class testWorkflows(MeetingNamurTestCase, mctw):
    """Tests the default workflows implemented in MeetingNamur."""

    def test_pm_WholeDecisionProcess(self):
        """
            This test covers the whole decision workflow. It begins with the
            creation of some items, and ends by closing a meeting.
            This call 1 sub tests because college wf and council af are the same
        """
        self._testWholeDecisionProcessCollege()

    def _testWholeDecisionProcessCollege(self):
        '''This test covers the whole decision workflow. It begins with the
           creation of some items, and ends by closing a meeting.'''
        # pmCreator1 creates an item
        self._activate_wfas(
            ('namur_meetingmanager_may_not_edit_decision_project',),
            keep_existing=True
        )
        self.changeUser('pmCreator1')
        item1 = self.create('MeetingItem', title='The first item')
        self.addAnnex(item1)
        # manager add decision annex because only manager or meeting manager can add it
        self.changeUser('pmManager')
        self.addAnnex(item1, relatedTo='item_decision')
        self.changeUser('pmCreator1')
        self.do(item1, 'propose')
        self.failIf(self.transitions(item1))  # He may trigger no more action
        self.failIf(self.hasPermission('PloneMeeting: Add annex', item1))
        # pmManager creates a meeting
        self.changeUser('pmManager')
        meeting = self.create('Meeting', date=DateTime('2007/12/11 09:00:00').asdatetime())
        self.addAnnex(item1, relatedTo='item_decision')
        # pmCreator2 creates and proposes an item
        self.changeUser('pmCreator2')
        item2 = self.create('MeetingItem', title='The second item',
                            preferredMeeting=meeting.UID())
        self.do(item2, 'propose')
        # pmReviewer1 validates item1
        self.changeUser('pmReviewer1')
        self.addAnnex(item1, relatedTo='item_decision')
        self.changeUser('pmReviewer1')
        self.do(item1, 'validate')
        self.assertRaises(Unauthorized, self.addAnnex, item1, relatedTo='item_decision')
        self.failIf(self.hasPermission('PloneMeeting: Add annex', item1))
        # pmManager inserts item1 into the meeting and publishes it
        self.changeUser('pmManager')
        managerAnnex = self.addAnnex(item1)
        self.portal.restrictedTraverse('@@delete_givenuid')(managerAnnex.UID())
        self.do(item1, 'present')
        # Now reviewers can't add annexes anymore
        self.changeUser('pmReviewer1')
        self.assertRaises(Unauthorized, self.addAnnex, item2)
        # meeting is frozen
        self.changeUser('pmManager')
        self.do(meeting, 'freeze')  # publish in pm forkflow
        # pmReviewer2 validates item2
        self.changeUser('pmReviewer2')
        self.do(item2, 'validate')
        # pmManager inserts item2 into the meeting, as late item, and adds an
        # annex to it
        self.changeUser('pmManager')
        self.do(item2, 'present')
        self.addAnnex(item2)
        # So now we should have 3 normal item (2 recurring + 1) and one late item in the meeting
        self.failUnless(len(meeting.get_items()) == 4)
        self.failUnless(len(meeting.get_items(list_types='late')) == 1)
        # pmManager adds a decision to item1 and freezes the meeting
        self.changeUser('pmManager')
        item1.setDecision(self.decisionText)
        # pmManager adds a decision for item2, decides and closes the meeting
        self.changeUser('pmManager')
        item2.setDecision(self.decisionText)
        self.addAnnex(item2, relatedTo='item_decision')
        self.do(meeting, 'decide')
        self.failIf(len(self.transitions(meeting)) != 2)
        self.do(meeting, 'close')

    def test_pm_FreezeMeeting(self):
        """
           When we freeze a meeting, every presented items will be frozen
           too and their state will be set to 'itemfrozen'.  When the meeting
           come back to 'created', every items will be corrected and set in the
           'presented' state
        """
        # First, define recurring items in the meeting config
        self.changeUser('pmManager')
        #create a meeting
        meeting = self.create('Meeting', date=DateTime('2007/12/11 09:00:00').asdatetime())
        #create 2 items and present them to the meeting
        item1 = self.create('MeetingItem', title='The first item')
        self.do(item1, 'propose')
        self.do(item1, 'validate')
        self.do(item1, 'present')
        item2 = self.create('MeetingItem', title='The second item')
        self.do(item2, 'propose')
        self.do(item2, 'validate')
        self.do(item2, 'present')
        wftool = self.portal.portal_workflow
        # every presented items are in the 'presented' state
        self.assertEquals('presented', wftool.getInfoFor(item1, 'review_state'))
        self.assertEquals('presented', wftool.getInfoFor(item2, 'review_state'))
        # every items must be in the 'itemfrozen' state if we freeze the meeting
        self.do(meeting, 'freeze')
        self.assertEquals('itemfrozen', wftool.getInfoFor(item1, 'review_state'))
        self.assertEquals('itemfrozen', wftool.getInfoFor(item2, 'review_state'))
        # when correcting the meeting back to created, the items must be corrected
        # back to "presented"
        self.do(meeting, 'backToCreated')
        # when a point is in 'itemfrozen' it's must return in presented state
        # because in import_datea we define a transition if meeting  return in created state
        self.assertEquals('presented', wftool.getInfoFor(item1, 'review_state'))
        self.assertEquals('presented', wftool.getInfoFor(item2, 'review_state'))

    def test_pm_WorkflowPermissions(self):
        """Bypass this test..."""
        pm_logger.info("Bypassing , {0} not used in MeetingNamur".format(
            self._testMethodName))

    def test_pm_RecurringItems(self):
        """Bypass this test..."""
        pm_logger.info("Bypassing , {0} not used in MeetingNamur".format(
            self._testMethodName))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testWorkflows, prefix='test_pm_'))
    return suite
