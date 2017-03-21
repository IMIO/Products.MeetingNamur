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

from Products.PloneMeeting.tests.PloneMeetingTestCase import PloneMeetingTestCase
from Products.MeetingNamur.testing import MNA_TESTING_PROFILE_FUNCTIONAL
from Products.MeetingNamur.tests.helpers import MeetingNamurTestingHelpers

# monkey patch the MeetingConfig.wfAdaptations again because it is done in
# adapters.py but overrided by Products.MeetingCommunes here in the tests...
from Products.PloneMeeting.MeetingConfig import MeetingConfig
from Products.PloneMeeting.model import adaptations
from Products.MeetingNamur.adapters import customWfAdaptations
MeetingConfig.wfAdaptations = customWfAdaptations
from Products.MeetingNamur.adapters import RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE

MeetingConfig.wfAdaptations = customWfAdaptations
adaptations.RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE = RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE

class MeetingNamurTestCase(PloneMeetingTestCase, MeetingNamurTestingHelpers):
    """Base class for defining MeetingNamur test cases."""

    layer = MNA_TESTING_PROFILE_FUNCTIONAL

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

    def setUp(self):
        PloneMeetingTestCase.setUp(self)
        self.meetingConfig = getattr(self.tool, 'meeting-config-college')
        self.meetingConfig2 = getattr(self.tool, 'meeting-config-council')

