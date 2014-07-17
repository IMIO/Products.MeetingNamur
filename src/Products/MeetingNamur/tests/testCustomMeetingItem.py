# -*- coding: utf-8 -*-
#
# File: testCustomMeetingItem.py
#
# Copyright (c) 2008 by PloneGov
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

from Products.MeetingNamur.tests.MeetingNamurTestCase import \
    MeetingNamurTestCase
from Products.PloneMeeting.tests.testMeetingItem import testMeetingItem as pmtmi
from DateTime import DateTime

class testCustomMeetingItem(MeetingNamurTestCase, pmtmi):
    """
        Tests the Meeting adapted methods
    """

    def _createMeetingWithItems(self):
        '''Create a meeting with a bunch of items.'''
        meetingDate = DateTime().strftime('%y/%m/%d %H:%M:%S')
        meeting = self.create('Meeting', date=meetingDate)
        item1 = self.create('MeetingItem')
        item1.setProposingGroup('developers')
        item2 = self.create('MeetingItem')
        item2.setProposingGroup('vendors')
        for item in (item1, item2):
            self.do(item, 'propose')
            self.do(item, 'validate')
            self.do(item, 'present')
        return meeting

    def test_GetMeetingsAcceptingItems(self):
        """
           We have to test this adapted method.
           It should only return meetings that are "created" or "frozen"
        """
        self.changeUser('pmManager')
        #create 4 meetings with items so we can play the workflow
        #will stay 'created'
        m1 = self._createMeetingWithItems()
        #go to state 'frozen'
        m2 = self._createMeetingWithItems()
        self.do(m2, 'freeze')
        #go to state 'decided'
        m3 = self._createMeetingWithItems()
        self.do(m3, 'freeze')
        self.do(m3, 'decide')
        #go to state 'closed'
        m4 = self._createMeetingWithItems()
        self.do(m4, 'freeze')
        self.do(m4, 'decide')
        self.do(m4, 'close')
        item = self.create('MeetingItem')
        #getMeetingsAcceptingItems should only return meetings 
        #that are 'created', 'frozen' or 'decided' for the meetingManager
        self.assertEquals([m.id for m in item.adapted().getMeetingsAcceptingItems()], [m1.id, m2.id, m3.id])
        #getMeetingsAcceptingItems should only return meetings 
        #that are 'created' or 'frozen' for the meetingMember
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        self.assertEquals([m.id for m in item.adapted().getMeetingsAcceptingItems()], [m1.id, m2.id])

    def test_GetCertifiedSignatures(self):
        '''Check that the certified signature is defined on developers group but not defined on vendors.'''
        #create an item for test
        self.changeUser('pmManager')
        meetingDate = DateTime('2008/06/12 08:00:00')
        self.create('Meeting', date=meetingDate)
        #create items
        self.changeUser('pmCreator1')
        i1 = self.create('MeetingItem')
        i1.setProposingGroup('vendors')
        #before present in meeting, certfiedSignatures must be empty
        res, isGrpSign = i1.adapted().getCertifiedSignatures()
        self.assertEquals(res,'')
        self.assertEquals(isGrpSign,False)
        self.do(i1, 'propose')
        self.changeUser('pmReviewer1')
        self.do(i1, 'validate')
        self.changeUser('pmManager')
        self.do(i1, 'present')
        #no signatures defined for vendors group, get meetingconfig signature
        res, isGrpSign = i1.adapted().getCertifiedSignatures()
        self.assertEquals(res,'Pierre Dupont, Bourgmestre - Charles Exemple, 1er Echevin')
        self.assertEquals(isGrpSign,False)
        self.changeUser('pmCreator1')
        i2 = self.create('MeetingItem')
        i2.setProposingGroup('developers')
        #before present in meeting, certfiedSignatures must be empty
        res, isGrpSign = i2.adapted().getCertifiedSignatures()
        self.assertEquals(res,'')
        self.assertEquals(isGrpSign,False)
        self.do(i2, 'propose')
        self.changeUser('pmReviewer1')
        self.do(i2, 'validate')
        self.changeUser('pmManager')
        self.do(i2, 'present')
        #signatures defined for developers group, get it
        res, isGrpSign = i2.adapted().getCertifiedSignatures()
        self.assertEquals(res,'developers signatures')
        self.assertEquals(isGrpSign,True)

    def test_GetEchevinsForProposingGroup(self):
        '''Check a meetingItem for developers group return an echevin (the Same group in our case)
           and a meetingItem for vendors return no echevin.'''
        #create an item for test
        self.changeUser('pmManager')
        meetingDate = DateTime('2008/06/12 08:00:00')
        self.create('Meeting', date=meetingDate)
        #create items
        self.changeUser('pmCreator1')
        i1 = self.create('MeetingItem')
        i1.setProposingGroup('vendors')
        #for vendor, certfiedSignatures must be empty
        res = i1.adapted().getEchevinsForProposingGroup()
        self.assertEquals(res,[])
        self.changeUser('pmCreator1')
        i2 = self.create('MeetingItem')
        i2.setProposingGroup('developers')
        #for developer, certfiedSignatures must be equal to 
        res = i2.adapted().getEchevinsForProposingGroup()
        self.assertEquals(res,['developers'])

    def test_listGrpBudgetInfosAdviser(self):
        '''Check if the list of groups that can be selected on an item to modify budgetInfos field
        correspond to group with accronym start with DGF (finance and taxe))'''
        self.changeUser('pmCreator1')
        i1 = self.create('MeetingItem')
        list_GBIA = i1.listGrpBudgetInfosAdviser()
        from Products.Archetypes.atapi import DisplayList
        res = DisplayList([('', u'make_a_choice'), ('finances', u'Finances'), ('taxes', u'Taxes')])
        self.assertEquals(len(list_GBIA),3)
        self.assertEquals(list_GBIA,res)

    def test_onEdit(self):
        '''check MeetingBudgetImpactReviewer role on an item, when a group is choosen in BudgetInfosAdviser and state is, at least "itemFrozen".
           Retrieve role for other grp_budgetimpactreviewers
        '''
        self.changeUser('pmManager')
        m = self._createMeetingWithItems()        
        self.do(m, 'freeze')
        item = m.getItems()[0]
        #no MeetingBudgetImpactReviewer in rôle
        self.assertEquals((u'developers_budgetimpactreviewers', ('MeetingObserverLocal', 'MeetingBudgetImpactReviewer')) in item.get_local_roles(),False)
        self.assertEquals((u'vendors_budgetimpactreviewers', ('MeetingObserverLocal', 'MeetingBudgetImpactReviewer')) in item.get_local_roles(),False)
        self.assertEquals((u'finances_budgetimpactreviewers', ('MeetingObserverLocal', 'MeetingBudgetImpactReviewer')) in item.get_local_roles(),False)
        self.assertEquals((u'taxes_budgetimpactreviewers', ('MeetingObserverLocal', 'MeetingBudgetImpactReviewer')) in item.get_local_roles(),False)
        item.setGrpBudgetInfos(('finances',))
        item.adapted().onEdit(True)
        #MeetingBudgetImpactReviewer role define for finance (only)
        self.assertEquals((u'developers_budgetimpactreviewers', ('MeetingObserverLocal', 'MeetingBudgetImpactReviewer')) in item.get_local_roles(),False)
        self.assertEquals((u'vendors_budgetimpactreviewers', ('MeetingObserverLocal', 'MeetingBudgetImpactReviewer')) in item.get_local_roles(),False)        
        self.assertEquals((u'finances_budgetimpactreviewers', ('MeetingObserverLocal', 'MeetingBudgetImpactReviewer')) in item.get_local_roles(),True)
        self.assertEquals((u'taxes_budgetimpactreviewers', ('MeetingObserverLocal', 'MeetingBudgetImpactReviewer')) in item.get_local_roles(),False)        
