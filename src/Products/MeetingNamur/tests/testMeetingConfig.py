# -*- coding: utf-8 -*-
#
# File: testMeetingConfig.py
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

from Products.MeetingCommunes.tests.testMeetingConfig import testMeetingConfig as mctmc
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase


class testMeetingConfig(MeetingNamurTestCase, mctmc):
    '''Tests the MeetingConfig class methods.'''

    def test_pm_SearchItemsToValidateOfEveryReviewerLevelsAndLowerLevels(self):
        '''Not sense... One validation level and prevalidation wfadaptation is not avalaible'''
        pass

    def test_pm_SearchItemsToValidateOfHighestHierarchicLevel(self):
        '''Not sense... One validation level and prevalidation wfadaptation is not avalaible'''
        pass

    def test_pm_SearchItemsToValidateOfMyReviewerGroups(self):
        '''Not sense... One validation level and prevalidation wfadaptation is not avalaible'''
        pass


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testMeetingConfig, prefix='test_pm_'))
    return suite
