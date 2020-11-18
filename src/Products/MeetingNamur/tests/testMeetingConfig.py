# -*- coding: utf-8 -*-
#
# File: testMeetingConfig.py
#
# GNU General Public License (GPL)
#

from Products.MeetingCommunes.tests.testMeetingConfig import testMeetingConfig as mctmc
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase
from Products.PloneMeeting.tests.PloneMeetingTestCase import pm_logger


class testMeetingConfig(MeetingNamurTestCase, mctmc):
    '''Tests the MeetingConfig class methods.'''

    def test_pm_SearchItemsToValidateOfEveryReviewerLevelsAndLowerLevels(self):
        '''Not sense... One validation level and prevalidation wfadaptation is not avalaible'''
        pm_logger.info("Bypassing , {0} not used in MeetingNamur".format(
            self._testMethodName))

    def test_pm_SearchItemsToValidateOfHighestHierarchicLevel(self):
        '''Not sense... One validation level and prevalidation wfadaptation is not avalaible'''
        pm_logger.info("Bypassing , {0} not used in MeetingNamur".format(
            self._testMethodName))

    def test_pm_SearchItemsToValidateOfMyReviewerGroups(self):
        '''Not sense... One validation level and prevalidation wfadaptation is not avalaible'''
        pm_logger.info("Bypassing , {0} not used in MeetingNamur".format(
            self._testMethodName))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testMeetingConfig, prefix='test_pm_'))
    return suite
