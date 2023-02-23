# -*- coding: utf-8 -*-
#
# File: testAnnexes.py
#
# Copyright (c) 2007-2015 by Imio.be
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

from AccessControl import Unauthorized
from DateTime import DateTime
from plone import api
from Products.MeetingCommunes.tests.testAnnexes import testAnnexes as mcta
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase
from Products.PloneMeeting.tests.PloneMeetingTestCase import pm_logger
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent


class testAnnexes(MeetingNamurTestCase, mcta):
    ''' '''

    def test_pm_ParentModificationDateUpdatedWhenAnnexChanged(self):
        """When an annex is added/modified/removed, the parent modification date is updated."""

        catalog = api.portal.get_tool('portal_catalog')

        def _check_parent_modified(parent, parent_modified, annex):
            """ """
            parent_uid = parent.UID()
            # modification date was updated
            self.assertNotEqual(parent_modified, item.modified())
            parent_modified = parent.modified()
            self.assertEqual(catalog(UID=parent_uid)[0].modified, parent_modified)

            # edit the annex
            notify(ObjectModifiedEvent(annex))
            # modification date was updated
            self.assertNotEqual(parent_modified, item.modified())
            parent_modified = parent.modified()
            self.assertEqual(catalog(UID=parent_uid)[0].modified, parent_modified)

            # remove an annex
            self.portal.restrictedTraverse('@@delete_givenuid')(annex.UID())
            # modification date was updated
            self.assertNotEqual(parent_modified, item.modified())
            parent_modified = parent.modified()
            self.assertEqual(catalog(UID=parent_uid)[0].modified, parent_modified)

        # on MeetingItem
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        parent_modified = item.modified()
        self.assertEqual(catalog(UID=item.UID())[0].modified, parent_modified)
        # add an annex
        annex = self.addAnnex(item)
        _check_parent_modified(item, parent_modified, annex)
        # add a decision annex
        self.changeUser('admin')
        decision_annex = self.addAnnex(item, relatedTo='item_decision')
        self.changeUser('pmCreator1')
        _check_parent_modified(item, parent_modified, decision_annex)

        # on Meeting
        self.changeUser('pmManager')
        meeting = self.create('Meeting', date=DateTime('2018/03/19').asdatetime())
        parent_modified = meeting.modified()
        self.assertEqual(catalog(UID=meeting.UID())[0].modified, parent_modified)
        # add an annex
        annex = self.addAnnex(meeting)
        _check_parent_modified(meeting, parent_modified, annex)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testAnnexes, prefix='test_pm_'))
    return suite
