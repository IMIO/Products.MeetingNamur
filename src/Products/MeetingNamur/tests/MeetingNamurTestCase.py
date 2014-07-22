# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2010 by PloneGov
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

from Products.MeetingCommunes.tests.MeetingCommunesTestCase import MeetingCommunesTestCase
from Products.MeetingNamur.testing import MNA_TEST_PROFILE_FUNCTIONAL
from Products.MeetingNamur.tests.helpers import MeetingNamurTestingHelpers

# monkey patch the MeetingConfig.wfAdaptations again because it is done in
# adapters.py but overrided by Products.MeetingCommunes here in the tests...
from Products.PloneMeeting.MeetingConfig import MeetingConfig
from Products.MeetingNamur.adapters import customWfAdaptations
MeetingConfig.wfAdaptations = customWfAdaptations


class MeetingNamurTestCase(MeetingCommunesTestCase, MeetingNamurTestingHelpers):
    """Base class for defining MeetingNamur test cases."""

    layer = MNA_TEST_PROFILE_FUNCTIONAL

    def _createFinanceGroups(self):
        """
           Create the finance groups.
        """
        financeGroupsData = ({'id': 'finances',
                              'title': 'Finances',
                              'acronym': 'DGF', },
                             {'id': 'taxes',
                              'title': 'Taxes',
                              'acronym': 'DGF - Taxes', },
                             )

        for financeGroup in financeGroupsData:
            if not hasattr(self.tool, financeGroup['id']):
                newGroupId = self.tool.invokeFactory('MeetingGroup',
                                                     id=financeGroup['id'],
                                                     title=financeGroup['title'],
                                                     acronym=financeGroup['acronym'], )
                newGroup = getattr(self.tool, newGroupId)
                newGroup.processForm(values={'dummy': None})


# this is necessary to execute base test
# test_tescasesubproduct_VerifyTestFiles from PloneMeeting
def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(MeetingCommunesTestCase, prefix='test_testcasesubproduct_'))
    return suite