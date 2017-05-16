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

from imio.actionspanel.interfaces import IContentDeletable
from Products.CMFCore.permissions import DeleteObjects

from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase
from Products.PloneMeeting.tests.testAnnexes import testAnnexes as pmta



class testAnnexes(MeetingNamurTestCase, pmta):
    ''' '''


    def test_pm_DecisionAnnexesDeletableByOwner(self):
        """annexDecision may be deleted by the Owner, aka the user that added the annex."""
        cfg = self.meetingConfig
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        item.setDecision('<p>Decision</p>')
        self.validateItem(item)
        # when an item is 'accepted', the MeetingMember may add annexDecision
        self.changeUser('pmManager')
        meeting = self.create('Meeting', date=DateTime('2016/11/11'))
        self.presentItem(item)
        self.decideMeeting(meeting)
        self.do(item, 'accept')
        self.assertEqual(item.queryState(), 'accepted')
        # creator can't add decision annex
        self.changeUser('pmCreator1')
        self.assertRaises(Unauthorized, self.addAnnex, item, relatedTo='item_decision')
        # manager can
        self.changeUser('pmManager')
        decisionAnnex1 = self.addAnnex(item, relatedTo='item_decision')
        self.assertTrue(decisionAnnex1 in item.objectValues())
        # doable if cfg.ownerMayDeleteAnnexDecision is True
        self.assertFalse(cfg.getOwnerMayDeleteAnnexDecision())
        self.assertRaises(Unauthorized, item.restrictedTraverse('@@delete_givenuid'), decisionAnnex1.UID())
        cfg.setOwnerMayDeleteAnnexDecision(True)
        item.restrictedTraverse('@@delete_givenuid')(decisionAnnex1.UID())
        self.assertFalse(decisionAnnex1 in item.objectValues())
        # add an annex and another user having same groups for item can not remove it
        decisionAnnex2 = self.addAnnex(item, relatedTo='item_decision')
        self.changeUser('pmCreator1b')
        self.assertRaises(Unauthorized, item.restrictedTraverse('@@delete_givenuid'), decisionAnnex2.UID())

    def test_pm_AnnexesDeletableByItemEditor(self):
        """annex/annexDecision may be deleted if user may edit the item."""
        # not sense


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testAnnexes, prefix='test_pm_'))
    return suite
