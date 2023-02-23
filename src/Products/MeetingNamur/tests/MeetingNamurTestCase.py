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

from Products.MeetingNamur.testing import MNA_TESTING_PROFILE_FUNCTIONAL
from Products.MeetingNamur.tests.helpers import MeetingNamurTestingHelpers

class MeetingNamurTestCase(MeetingCommunesTestCase, MeetingNamurTestingHelpers):
    """Base class for defining MeetingNamur test cases."""

    layer = MNA_TESTING_PROFILE_FUNCTIONAL
    subproductIgnoredTestFiles = ['testPerformances.py',
                                  'testVotes.py',
                                  'test_robot.py']

    def setUp(self):
        MeetingCommunesTestCase.setUp(self)
        self.meetingConfig = getattr(self.tool, 'meeting-config-college')
        self.meetingConfig2 = getattr(self.tool, 'meeting-config-council')
