# -*- coding: utf-8 -*-
#
# File: testViews.py
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

from Products.MeetingCommunes.tests.testViews import testViews as mctv
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase


class testViews(MeetingNamurTestCase, mctv):
    ''' '''


    def test_pm_CreateItemFromTemplate(self):
        '''
          Test the createItemFromTemplate functionnality triggered from the plonemeeting portlet.
        '''
        cfg = self.meetingConfig
        self.changeUser('pmCreator1')
        self.getMeetingFolder()
        folder = getattr(self.portal.Members.pmCreator1.mymeetings, self.meetingConfig.getId())
        itemTemplateView = folder.restrictedTraverse('createitemfromtemplate')
        # the template we will use
        itemTemplates = cfg.getItemTemplates(filtered=True)
        itemTemplate = itemTemplates[0].getObject()
        self.assertTrue(itemTemplate.portal_type == cfg.getItemTypeName(configType='MeetingItemTemplate'))
        itemTemplateUID = itemTemplate.UID()
        # for now, no items in the user folder
        self.assertTrue(not folder.objectIds('MeetingItem'))
        newItem = itemTemplateView.createItemFromTemplate(itemTemplateUID)
        self.assertTrue(newItem.portal_type == cfg.getItemTypeName())
        # the new item is the itemTemplate clone
        self.assertTrue(newItem.Title() == itemTemplate.Title())
        self.assertTrue(newItem.Description() == itemTemplate.Description())
        # for Namur, the decision is always empty at creation
        self.assertTrue(newItem.getDecision() == '<p>&nbsp;</p>')
        # and it has been created in the user folder
        self.assertTrue(newItem.getId() in folder.objectIds())
        # now check that the user can use a 'secret' item template if no proposing group is selected on it
        self.changeUser('admin')
        itemTemplate.setPrivacy('secret')
        # an itemTemplate can have no proposingGroup, it does validate
        itemTemplate.setProposingGroup('')
        self.failIf(itemTemplate.validate_proposingGroup(''))
        # use this template
        self.changeUser('pmCreator1')
        newItem2 = itemTemplateView.createItemFromTemplate(itemTemplateUID)
        self.assertTrue(newItem2.portal_type == cfg.getItemTypeName())
        # item has been created with a filled proposing group
        # and privacy is still ok
        self.assertTrue(newItem2.getId() in folder.objectIds())
        userGroups = self.tool.get_orgs_for_user(suffixes=['creators'])
        self.assertEqual(newItem2.getProposingGroup(), userGroups[0].UID())
        self.assertEqual(newItem2.getPrivacy(), itemTemplate.getPrivacy())

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testViews, prefix='test_pm_'))
    return suite
