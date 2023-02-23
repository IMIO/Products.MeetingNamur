# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta

from AccessControl import Unauthorized
from Products.MeetingCommunes.tests.testCustomMeetingItem import testCustomMeetingItem as mctcmi
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase


class testCustomMeetingItem(MeetingNamurTestCase, mctcmi):
    """
        Tests the Meeting adapted methods
    """

    def test_onEdit(self):
        """check MeetingBudgetImpactReviewer role on an item, when a group is choosen in BudgetInfosAdviser
        and state is, at least "itemFrozen". Retrieve role for other grp_budgetimpactreviewers
        """
        self.changeUser('pmManager')
        m = self._createMeetingWithItems()
        self.do(m, 'freeze')
        item = m.get_items()[0]
        # no MeetingBudgetImpactReviewer in rôle
        self.assertEquals((u'developers_budgetimpactreviewers', (
            'Reader', 'MeetingBudgetImpactReviewer')) in item.get_local_roles(), False)
        self.assertEquals((u'vendors_budgetimpactreviewers', (
            'Reader', 'MeetingBudgetImpactReviewer')) in item.get_local_roles(), False)
        self.assertEquals((u'finances_budgetimpactreviewers', (
            'Reader', 'MeetingBudgetImpactReviewer')) in item.get_local_roles(), False)
        self.assertEquals((u'taxes_budgetimpactreviewers', (
            'Reader', 'MeetingBudgetImpactReviewer')) in item.get_local_roles(), False)
        item.setGrpBudgetInfos(('finances',))
        item.adapted().onEdit(True)
        # MeetingBudgetImpactReviewer role define for finance (only)
        self.assertEquals((u'developers_budgetimpactreviewers', (
            'Reader', 'MeetingBudgetImpactReviewer')) in item.get_local_roles(), False)
        self.assertEquals((u'vendors_budgetimpactreviewers', (
            'Reader', 'MeetingBudgetImpactReviewer')) in item.get_local_roles(), False)
        self.assertEquals((u'finances_budgetimpactreviewers', (
            'Reader', 'MeetingBudgetImpactReviewer')) in item.get_local_roles(), True)
        self.assertEquals((u'taxes_budgetimpactreviewers', (
            'Reader', 'MeetingBudgetImpactReviewer')) in item.get_local_roles(), False)

    def test_manageItemCertifiedSignatures(self):
        """
          This tests the form that manage itemCertifiedSignatures and that can apply it on item.
        """
        self.changeUser('admin')
        # make items inserted in a meeting inserted in this order
        self.meetingConfig.insertingMethodsOnAddItem = ({'insertingMethod': 'at_the_end', 'reverse': '0'}, )
        # remove recurring items if any as we are playing with item number here under
        self._removeConfigObjectsFor(self.meetingConfig)
        # a user create an item and we insert it into a meeting
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        item.setDecision('<p>A decision</p>')
        self.changeUser('pmManager')
        meeting = self.create('Meeting', date=datetime.now() + timedelta(days=1))
        # define an assembly on the meeting
        meeting.assembly = 'Meeting assembly'
        meeting.signatures = 'Meeting signatures'
        self.presentItem(item)
        # make the form item_assembly_default works
        self.request['PUBLISHED'].context = item
        self.changeUser('pmCreator1')
        formCertifiedSignatures = item.restrictedTraverse('@@manage_item_certified_signatures_form').form_instance
        # for now, the itemCertifiedSignatures fields are not used, so it raises Unauthorized
        self.assertRaises(Unauthorized, formCertifiedSignatures.update)
        # current user must be at least MeetingManager to use this
        self.changeUser('admin')
        formCertifiedSignatures = item.restrictedTraverse('@@manage_item_certified_signatures_form').form_instance
        formCertifiedSignatures.update()
        # by default, itemCertifiedSignatures is not define
        self.assertEquals(item.getItemCertifiedSignatures(), '')
        # now use the form to change the item itemCertifiedSignatures
        self.changeUser('pmManager')
        self.freezeMeeting(meeting)
        self.do(meeting, 'decide')
        self.do(item, 'accept')
        self.changeUser('pmCreator1')
        formCertifiedSignatures = item.restrictedTraverse('@@manage_item_certified_signatures_form').form_instance
        formCertifiedSignatures.update()
        self.request.form['form.widgets.item_certified_signatures'] = u'Item certified signatures'
        formCertifiedSignatures.handleApplyItemCertifiedSignatures(formCertifiedSignatures, None)
        self.assertEquals(item.getItemCertifiedSignatures(), 'Item certified signatures')
        # we can change this field in closed meeting
        self.changeUser('pmManager')
        self.do(meeting, 'close')
        self.changeUser('pmCreator1')
        formCertifiedSignatures = item.restrictedTraverse('@@manage_item_certified_signatures_form').form_instance
        self.request.form['form.widgets.item_certified_signatures'] = u'Item certified signatures - 2'
        formCertifiedSignatures.update()
        formCertifiedSignatures.handleApplyItemCertifiedSignatures(formCertifiedSignatures, None)
        self.assertEquals(item.getItemCertifiedSignatures(), 'Item certified signatures - 2')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testCustomMeetingItem, prefix='test_'))
    return suite
