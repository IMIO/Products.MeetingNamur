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
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase
from Products.MeetingCommunes.tests.testAnnexes import testAnnexes as mcta
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent



class testAnnexes(MeetingNamurTestCase, mcta):
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
        pass

    def test_pm_CategorizedAnnexesShowMethods(self):
        """Test the @@categorized-annexes view."""
        cfg = self.meetingConfig
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        view = item.restrictedTraverse('@@categorized-annexes')
        # both annex and annexDecision are displayed and addable
        self.assertTrue(view.showAddAnnex())
        # for Namur, only MeetingManager can add decision'annex
        self.assertFalse(view.showAddAnnexDecision())
        self.changeUser('pmManager')
        self.assertTrue(view.showAddAnnexDecision())
        self.changeUser('pmCreator1')
        self.assertTrue(view.showDecisionAnnexesSection())
        # add an annex and an annexDecision
        self.addAnnex(item)
        self.changeUser('pmManager')
        annexDecision = self.addAnnex(item, relatedTo='item_decision')
        self.changeUser('pmCreator1')
        self.assertTrue(view.showAddAnnex())
        self.assertFalse(view.showAddAnnexDecision())
        self.assertTrue(view.showAnnexesSection())
        self.assertTrue(view.showDecisionAnnexesSection())
        # propose item, annex sections are still shown but not addable
        self.proposeItem(item)
        self.assertFalse(view.showAddAnnex())
        self.assertFalse(view.showAddAnnexDecision())
        self.assertTrue(view.showAnnexesSection())
        self.assertTrue(view.showDecisionAnnexesSection())

        # annexDecision section is shown if annexDecision are stored or if
        # annexDecision annex types are available (active), disable the annexDecision annex types
        for annex_type in cfg.annexes_types.item_decision_annexes.objectValues():
            annex_type.enabled = False
            annex_type.reindexObject(idxs=['enabled'])
        # view._annexDecisionCategories is memoized
        view = item.restrictedTraverse('@@categorized-annexes')
        # showDecisionAnnexesSection still True because annexDecision exists
        self.assertTrue(view.showDecisionAnnexesSection())
        self.deleteAsManager(annexDecision.UID())
        # view._annexDecisionCategories is memoized
        view = item.restrictedTraverse('@@categorized-annexes')
        self.assertFalse(view.showDecisionAnnexesSection())

    def test_pm_AnnexRestrictShownAndEditableAttributes(self):
        """Test MeetingConfig.annexRestrictShownAndEditableAttributes
           that defines what annex attributes are displayed/editable only to MeetingManagers."""
        # enable every attributes
        self.changeUser('siteadmin')
        cfg = self.meetingConfig
        cfg.setAnnexRestrictShownAndEditableAttributes(())
        config = cfg.annexes_types.item_annexes
        annex_attr_names = (
            'confidentiality_activated',
            'signed_activated',
            'publishable_activated',
            'to_be_printed_activated')
        # enable every attr for annex, none for annexDecision
        for attr_name in annex_attr_names:
            setattr(config, attr_name, True)

        # helper check method
        annex_attr_change_view_names = (
            '@@iconified-confidential',
            '@@iconified-signed',
            '@@iconified-publishable',
            '@@iconified-print')

        def _check(annexes_table,
                   annex,
                   annex_decision,
                   displayed=annex_attr_change_view_names,
                   editable=annex_attr_change_view_names):
            ''' '''
            # nothing displayed for annexDecision
            for view_name in displayed:
                self.assertTrue(view_name in annexes_table.table_render(portal_type='annex'))
                self.assertFalse(view_name in annexes_table.table_render(portal_type='annexDecision'))
            for view_name in editable:
                self.assertTrue(annex.restrictedTraverse(view_name)._may_set_values({}))
                self.assertFalse(annex_decision.restrictedTraverse(view_name)._may_set_values({}))

        # xxx Namur, creator can't create decsion, annexe
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        annex = self.addAnnex(item)
        self.assertRaises(Unauthorized, self.addAnnex, item, relatedTo='item_decision')
        self.changeUser('admin')
        annex_decision = self.addAnnex(item, relatedTo='item_decision')
        self.changeUser('pmCreator1')
        annexes_table = item.restrictedTraverse('@@iconifiedcategory')
        # everything displayed/editable by user
        self.assertEqual(cfg.getAnnexRestrictShownAndEditableAttributes(), ())
        _check(annexes_table, annex, annex_decision)
        # confidential no more editable but viewable
        cfg.setAnnexRestrictShownAndEditableAttributes(('confidentiality_edit'))
        list_editable_annex_attr_change_view_names = list(annex_attr_change_view_names)
        list_editable_annex_attr_change_view_names.remove('@@iconified-confidential')
        _check(annexes_table, annex, annex_decision, editable=list_editable_annex_attr_change_view_names)
        # confidential and signed no more editable but viewable
        cfg.setAnnexRestrictShownAndEditableAttributes(('confidentiality_edit', 'signed_edit'))
        list_editable_annex_attr_change_view_names.remove('@@iconified-signed')
        _check(annexes_table, annex, annex_decision, editable=list_editable_annex_attr_change_view_names)
        # when someting not displayed, not editable automatically
        cfg.setAnnexRestrictShownAndEditableAttributes(('confidentiality_edit',
                                                        'signed_edit',
                                                        'publishable_display'))
        list_editable_annex_attr_change_view_names.remove('@@iconified-publishable')
        list_displayed_annex_attr_change_view_names = list(annex_attr_change_view_names)
        list_displayed_annex_attr_change_view_names.remove('@@iconified-publishable')
        _check(annexes_table, annex, annex_decision,
               editable=list_editable_annex_attr_change_view_names,
               displayed=list_displayed_annex_attr_change_view_names)

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
        meeting = self.create('Meeting', date=DateTime('2018/03/19'))
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
