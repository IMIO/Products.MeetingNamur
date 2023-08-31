# -*- coding: utf-8 -*-
#
# GNU General Public License (GPL)
#

from Products.MeetingCommunes.tests.testViews import testViews as mctv
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase


class testViews(MeetingNamurTestCase, mctv):
    ''' '''


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testViews, prefix='test_pm_'))
    return suite
