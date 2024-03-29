# -*- coding: utf-8 -*-
#
# File: testMeetingConfig.py
#
# Copyright (c) 2015 by Imio.be
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

from Products.MeetingCommunes.tests.testSearches import testSearches as mcts
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase
from Products.PloneMeeting.tests.PloneMeetingTestCase import pm_logger


class testSearches(MeetingNamurTestCase, mcts):
    """Test searches."""

    def test_pm_SearchItemsToCorrectToValidateOfHighestHierarchicLevel(self):
        '''Not used yet...'''
        pm_logger.info("Bypassing , {0} not used in MeetingNamur".format(
            self._testMethodName))

    def test_pm_SearchItemsToCorrectToValidateOfEveryReviewerGroups(self):
        '''Not used yet...'''
        pm_logger.info("Bypassing , {0} not used in MeetingNamur".format(
            self._testMethodName))

    def test_pm_SearchItemsToValidateOfHighestHierarchicLevel(self):
        """Not sense, only one level of validation"""
        pm_logger.info("Bypassing , {0} not used in MeetingNamur".format(
            self._testMethodName))

    def test_pm_SearchItemsToValidateOfMyReviewerGroups(self):
        """Not sense, only one level of validation"""
        pm_logger.info("Bypassing , {0} not used in MeetingNamur".format(
            self._testMethodName))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testSearches, prefix='test_pm_'))
    return suite
