# -*- coding: utf-8 -*-
#
# GNU General Public License (GPL)
#

from Products.MeetingCommunes.tests.testMeeting import testMeetingType as mctm
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase


class testMeetingType(MeetingNamurTestCase, mctm):
    """
        Tests the Meeting class methods.
    """


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testMeetingType, prefix='test_pm_'))
    return suite
