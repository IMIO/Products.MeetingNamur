# -*- coding: utf-8 -*-
#
# File: testAdvices.py
#
# Copyright (c) 2007-2012 by CommunesPlone.org
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
from datetime import datetime
from plone import api
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.permissions import View
from Products.MeetingCommunes.tests.testAdvices import testAdvices as mcta
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema.interfaces import RequiredMissing


class testAdvices(MeetingNamurTestCase, mcta):
    """Tests various aspects of advices management.
       Advices are enabled for PloneGov Assembly, not for PloneMeeting Assembly."""

    def test_pm_AddEditDeleteAdvices(self):
        '''This test the MeetingItem.getAdvicesGroupsInfosForUser method.
           MeetingItem.getAdvicesGroupsInfosForUser returns 2 lists : first with addable advices and
           the second with editable/deletable advices.'''
        # creator for group 'developers'
        self.changeUser('pmCreator1')
        # create an item and ask the advice of group 'vendors'
        data = {
            'title': 'Item to advice',
            'category': 'maintenance'
        }
        item1 = self.create('MeetingItem', **data)
        item1.setOptionalAdvisers((self.vendors_uid, ))
        item1._update_after_edit()
        # 'pmCreator1' has no addable nor editable advice to give
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([], []))
        self.changeUser('pmReviewer2')
        self.failIf(self.hasPermission(View, item1))
        self.changeUser('pmCreator1')
        self.proposeItem(item1)
        # a user able to View the item can not add an advice, even if he tries...
        self.assertRaises(Unauthorized,
                          createContentInContainer,
                          item1,
                          'meetingadvice')
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([], []))
        self.changeUser('pmReviewer2')
        # 'pmReviewer2' has one advice to give for 'vendors' and no advice to edit
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([(self.vendors_uid)], []))
        self.assertEquals(item1.hasAdvices(), False)
        # fields 'advice_type' and 'advice_group' are mandatory
        form = item1.restrictedTraverse('++add++meetingadvice').form_instance
        form.ti = self.portal.portal_types['meetingadvice']
        self.request['PUBLISHED'] = form
        form.update()
        errors = form.extractData()[1]
        self.assertEquals(errors[0].error, RequiredMissing('advice_group'))
        self.assertEquals(errors[1].error, RequiredMissing('advice_type'))
        # value used for 'advice_type' and 'advice_group' must be correct
        form.request.set('form.widgets.advice_type', u'wrong_value')
        errors = form.extractData()[1]
        self.assertEquals(errors[1].error, RequiredMissing('advice_type'))
        # but if the value is correct, the field renders correctly
        form.request.set('form.widgets.advice_type', u'positive')
        data = form.extractData()[0]
        self.assertEquals(data['advice_type'], u'positive')
        # regarding 'advice_group' value, only correct are the ones in the vocabulary
        # so using another will fail, for example, can not give an advice for another group
        form.request.set('form.widgets.advice_group', self.developers_uid)
        data = form.extractData()[0]
        self.assertFalse('advice_group' in data)
        # we can use the values from the vocabulary
        vocab = form.widgets.get('advice_group').terms.terms
        self.failUnless(self.vendors_uid in vocab)
        self.assertEqual(len(vocab), 1)
        # give the advice, select a valid 'advice_group' and save
        form.request.set('form.widgets.advice_group', self.vendors_uid)
        # the 3 fields 'advice_group', 'advice_type' and 'advice_comment' are handled correctly
        data = form.extractData()[0]
        self.assertTrue('advice_group' in data and
                        'advice_type' in data and
                        'advice_comment' in data and
                        'advice_row_id' in data and
                        'advice_observations' in data and
                        'advice_hide_during_redaction' in data)
        # we receive the 6 fields
        self.assertEqual(len(data), len(form.fields))
        form.request.form['advice_group'] = self.vendors_uid
        form.request.form['advice_type'] = u'positive'
        form.request.form['advice_comment'] = RichTextValue(u'My comment')
        form.createAndAdd(form.request.form)
        self.assertEquals(item1.hasAdvices(), True)
        # 'pmReviewer2' has no more addable advice (as already given) but has now an editable advice
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([], [(self.vendors_uid)]))
        # given advice is correctly stored
        self.assertEquals(item1.adviceIndex[self.vendors_uid]['type'], 'positive')
        self.assertEquals(item1.adviceIndex[self.vendors_uid]['comment'], u'My comment')
        self.changeUser('pmReviewer1')
        self.validateItem(item1)
        # now 'pmReviewer2' can't add (already given) an advice
        # but he can still edit the advice he just gave
        self.changeUser('pmReviewer2')
        self.failUnless(self.hasPermission(View, item1))
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([], [(self.vendors_uid)]))
        given_advice = getattr(item1, item1.adviceIndex[self.vendors_uid]['advice_id'])
        self.failUnless(self.hasPermission(ModifyPortalContent, given_advice))
        # another member of the same _advisers group may also edit the given advice
        self.changeUser('pmManager')
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([], [(self.vendors_uid)]))
        self.failUnless(self.hasPermission(ModifyPortalContent, given_advice))
        # if a user that can not remove the advice tries he gets Unauthorized
        self.changeUser('pmReviewer1')
        self.assertRaises(Unauthorized, item1.restrictedTraverse('@@delete_givenuid'), item1.meetingadvice.UID())
        # put the item back in a state where 'pmReviewer2' can remove the advice
        self.changeUser('pmManager')
        self.backToState(item1, self._stateMappingFor('proposed'))
        self.changeUser('admin')
        # xxx Namur, only admin can remove the advice
        item1.restrictedTraverse('@@delete_givenuid')(item1.meetingadvice.UID())
        self.changeUser('pmReviewer2')
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([(self.vendors_uid)], []))

        # if advices are disabled in the meetingConfig, getAdvicesGroupsInfosForUser is emtpy
        self.changeUser('admin')
        self.meetingConfig.setUseAdvices(False)
        self.changeUser('pmReviewer2')
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([], []))
        self.changeUser('admin')
        self.meetingConfig.setUseAdvices(True)

        # activate advices again and this time remove the fact that we asked the advice
        self.changeUser('pmReviewer2')
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([(self.vendors_uid)], []))
        self.changeUser('pmManager')
        item1.setOptionalAdvisers([])
        item1._update_after_edit()
        self.changeUser('pmReviewer2')
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([], []))


    def test_pm_MayTriggerGiveAdviceWhenItemIsBackToANotViewableState(self, ):
        '''Test that if an item is set back to a state the user that set it back can
           not view anymore, and that the advice turn from giveable to not giveable anymore,
           transitions triggered on advice that will 'giveAdvice'.'''
        cfg = self.meetingConfig
        # advice can be given when item is validated
        cfg.setItemAdviceStates((self._stateMappingFor('validated'), ))
        cfg.setItemAdviceEditStates((self._stateMappingFor('validated'), ))
        cfg.setItemAdviceViewStates((self._stateMappingFor('validated'), ))
        # create an item as vendors and give an advice as vendors on it
        # it is viewable by MeetingManager when validated
        self.changeUser('pmCreator2')
        item = self.create('MeetingItem')
        item.setOptionalAdvisers((self.vendors_uid, ))
        # validate the item and advice it
        self.validateItem(item)
        self.changeUser('pmReviewer2')
        createContentInContainer(item,
                                 'meetingadvice',
                                 **{'advice_group': self.vendors_uid,
                                    'advice_type': u'positive',
                                    'advice_comment': RichTextValue(u'My comment')})
        # make sure if a MeetingManager send the item back to 'proposed' it works...
        self.changeUser('pmManager')
        # do the back transition that send the item back to 'proposed'
        itemWF = self.wfTool.getWorkflowsFor(item)[0]
        backToProposedTr = None
        # make sure if a MeetingManager send the item back to 'proposed' it works...
        self.changeUser('pmManager')
        # xxx NAMUR do the back transition that send the item back to 'itemcreated'
        itemWF = self.wfTool.getWorkflowsFor(item)[0]
        backToCreatedTr = None
        for tr in self.transitions(item):
            # get the transition that ends to 'itemcreated'
            transition = itemWF.transitions[tr]
            if transition.new_state_id == self._stateMappingFor('itemcreated'):
                backToCreatedTr = tr
                break
        # this will work...
        self.do(item, backToCreatedTr)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testAdvices, prefix='test_pm_'))
    return suite
