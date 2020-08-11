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
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([(self.vendors_uid, u'Vendors')], []))
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
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([], [(self.vendors_uid, 'Vendors')]))
        # given advice is correctly stored
        self.assertEquals(item1.adviceIndex[self.vendors_uid]['type'], 'positive')
        self.assertEquals(item1.adviceIndex[self.vendors_uid]['comment'], u'My comment')
        self.changeUser('pmReviewer1')
        self.validateItem(item1)
        # now 'pmReviewer2' can't add (already given) an advice
        # but he can still edit the advice he just gave
        self.changeUser('pmReviewer2')
        self.failUnless(self.hasPermission(View, item1))
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([], [(self.vendors_uid, 'Vendors')]))
        given_advice = getattr(item1, item1.adviceIndex[self.vendors_uid]['advice_id'])
        self.failUnless(self.hasPermission(ModifyPortalContent, given_advice))
        # another member of the same _advisers group may also edit the given advice
        self.changeUser('pmManager')
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([], [(self.vendors_uid, 'Vendors')]))
        self.failUnless(self.hasPermission(ModifyPortalContent, given_advice))
        # if a user that can not remove the advice tries he gets Unauthorized
        self.changeUser('pmReviewer1')
        self.assertRaises(Unauthorized, item1.restrictedTraverse('@@delete_givenuid'), item1.meetingadvice.UID())
        # put the item back in a state where 'pmReviewer2' can remove the advice
        self.changeUser('pmManager')
        self.backToState(item1, self._stateMappingFor('proposed'))
        self.changeUser('admin')
        # xxx NAmur, only admin can remove the advice
        item1.restrictedTraverse('@@delete_givenuid')(item1.meetingadvice.UID())
        self.changeUser('pmReviewer2')
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([(self.vendors_uid, u'Vendors')], []))

        # if advices are disabled in the meetingConfig, getAdvicesGroupsInfosForUser is emtpy
        self.changeUser('admin')
        self.meetingConfig.setUseAdvices(False)
        self.changeUser('pmReviewer2')
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([], []))
        self.changeUser('admin')
        self.meetingConfig.setUseAdvices(True)

        # activate advices again and this time remove the fact that we asked the advice
        self.changeUser('pmReviewer2')
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([(self.vendors_uid, u'Vendors')], []))
        self.changeUser('pmManager')
        item1.setOptionalAdvisers([])
        item1._update_after_edit()
        self.changeUser('pmReviewer2')
        self.assertEquals(item1.getAdvicesGroupsInfosForUser(), ([], []))
    def test_pm_AdviceHistorizedIfGivenAndItemChanged(self):
        """When an advice is given, if it was not historized and an item richText field
           is changed, it is versioned and relevant item infos are saved.  This way we are sure that
           historized infos about item are the one when the advice was given.
           Moreover, advice is only versioned if it was modified since last version."""
        cfg = self.meetingConfig
        # item data are saved if cfg.historizeItemDataWhenAdviceIsGiven
        self.assertTrue(cfg.getHistorizeItemDataWhenAdviceIsGiven())
        # make sure we know what item rich text fields are enabled
        cfg.setUsedItemAttributes(('description', 'detailedDescription', 'motivation', ))
        cfg.setItemAdviceStates([self._stateMappingFor('proposed'), ])
        cfg.setItemAdviceEditStates([self._stateMappingFor('proposed'), ])
        cfg.setItemAdviceViewStates([self._stateMappingFor('proposed'), ])
        # default value of field 'advice_hide_during_redaction' is False
        self.assertFalse(cfg.getDefaultAdviceHiddenDuringRedaction())

        self.changeUser('pmCreator1')
        # create an item and ask the advice of group 'vendors'
        data = {
            'title': 'Item to advice',
            'category': 'maintenance',
            'optionalAdvisers': (self.vendors_uid, self.developers_uid, ),
            'description': '<p>Item description</p>',
        }
        item = self.create('MeetingItem', **data)
        item.setDetailedDescription('<p>Item detailed description</p>')
        item.setMotivation('<p>Item motivation</p>')
        item.setDecision('<p>Item decision</p>')
        self.proposeItem(item)
        # give advice
        self.changeUser('pmReviewer2')
        advice = createContentInContainer(item,
                                          'meetingadvice',
                                          **{'advice_group': self.vendors_uid,
                                             'advice_type': u'negative',
                                             'advice_hide_during_redaction': False,
                                             'advice_comment': RichTextValue(u'My comment')})
        # advice will be versioned if the item is edited
        # this is only the case if cfg.versionateAdviceIfGivenAndItemModified is True
        self.changeUser('siteadmin')
        cfg.setVersionateAdviceIfGivenAndItemModified(False)
        self.changeUser('pmReviewer1')
        pr = api.portal.get_tool('portal_repository')
        self.assertFalse(pr.getHistoryMetadata(advice))
        self.request.form['detailedDescription'] = '<p>Item detailed description not active</p>'
        item.processForm()
        self.assertEquals(item.getDetailedDescription(),
                          '<p>Item detailed description not active</p>')
        # it was not versioned because versionateAdviceIfGivenAndItemModified is False
        h_metadata = pr.getHistoryMetadata(advice)
        self.assertEquals(h_metadata, [])
        # activate and try again
        self.changeUser('siteadmin')
        cfg.setVersionateAdviceIfGivenAndItemModified(True)
        self.changeUser('pmReviewer1')
        item.processForm()
        # first version, item data was historized on it
        previous = pr.retrieve(advice, 0).object
        # we have item data before it was modified
        self.assertEquals(previous.historized_item_data,
                          [{'field_name': 'title',
                            'field_content': 'Item to advice'},
                           {'field_name': 'description',
                            'field_content': '<p>Item description</p>'},
                           {'field_name': 'detailedDescription',
                            'field_content': '<p>Item detailed description not active</p>'},
                           {'field_name': 'motivation',
                            'field_content': '<p>Item motivation</p>'},
                           {'field_name': 'decision',
                            'field_content': '<p>Item decision</p>'}])

        # when editing item a second time, if advice is not edited, it is not versioned uselessly
        self.request.form['detailedDescription'] = '<p>Item detailed description edited 2</p>'
        item.processForm({'detailedDescription': '<p>Item detailed description edited 2</p>'})
        self.assertEquals(item.getDetailedDescription(), '<p>Item detailed description edited 2</p>')
        h_metadata = pr.getHistoryMetadata(advice)
        self.assertEquals(h_metadata._available, [0])

        # when moving to 'validated', advice is 'adviceGiven', but not versioned again
        self.validateItem(item)
        h_metadata = pr.getHistoryMetadata(advice)
        self.assertEquals(h_metadata._available, [0])

        # but it is again if advice is edited
        self.changeUser('pmManager')
        self.backToState(item, self._stateMappingFor('proposed'))
        self.changeUser('pmReviewer2')
        notify(ObjectModifiedEvent(advice))
        self.changeUser('pmReviewer1')
        # validate item, this time advice is versioned again
        self.validateItem(item)
        h_metadata = pr.getHistoryMetadata(advice)
        self.assertEquals(h_metadata._available, [0, 1])

        # and once again back to proposed and edit item
        # not versioned because advice was not edited
        self.changeUser('pmManager')
        self.backToState(item, self._stateMappingFor('proposed'))
        self.changeUser('pmReviewer1')
        self.request.form['detailedDescription'] = '<p>Item detailed description edited 3</p>'
        item.processForm({'detailedDescription': '<p>Item detailed description edited 3</p>'})
        self.assertEquals(item.getDetailedDescription(), '<p>Item detailed description edited 3</p>')
        h_metadata = pr.getHistoryMetadata(advice)
        self.assertEquals(h_metadata._available, [0, 1])

        # right, back to proposed and use ajax edit
        self.changeUser('pmManager')
        self.backToState(item, self._stateMappingFor('proposed'))
        self.changeUser('pmReviewer2')
        notify(ObjectModifiedEvent(advice))
        self.changeUser('pmReviewer1')
        item.setFieldFromAjax('detailedDescription', '<p>Item detailed description edited 4</p>')
        self.assertEquals(item.getDetailedDescription(), '<p>Item detailed description edited 4</p>')
        # advice was versioned again
        h_metadata = pr.getHistoryMetadata(advice)
        self.assertEquals(h_metadata._available, [0, 1, 2])
        # we have item data before it was modified
        previous = pr.retrieve(advice, 2).object
        # xxx for Namur, decision is empty before presentation of item in meeting
        self.assertEquals(previous.historized_item_data,
                          [{'field_name': 'title',
                            'field_content': 'Item to advice'},
                           {'field_name': 'description',
                            'field_content': '<p>Item description</p>'},
                           {'field_name': 'detailedDescription',
                            'field_content': '<p>Item detailed description edited 3</p>'},
                           {'field_name': 'motivation',
                            'field_content': '<p>Item motivation</p>'},
                           {'field_name': 'decision',
                            'field_content': '<p>&nbsp;</p>'}])

        # advice are no more versionated when annex is added/removed
        annex = self.addAnnex(item)
        # was already versionated so no more
        h_metadata = pr.getHistoryMetadata(advice)
        self.assertEquals(h_metadata._available, [0, 1, 2])
        # right edit the advice and remove the annex
        self.changeUser('pmReviewer2')
        notify(ObjectModifiedEvent(advice))
        self.changeUser('pmReviewer1')
        self.deleteAsManager(annex.UID())
        # advice was not versioned again
        h_metadata = pr.getHistoryMetadata(advice)
        self.assertEquals(h_metadata._available, [0, 1, 2])
        # edit advice and add a new annex, advice will not be versionated
        self.changeUser('pmReviewer2')
        notify(ObjectModifiedEvent(advice))
        self.changeUser('pmReviewer1')
        annex = self.addAnnex(item)
        h_metadata = pr.getHistoryMetadata(advice)
        self.assertEquals(h_metadata._available, [0, 1, 2])

    def test_pm_AdviceHistorizedWithItemDataWhenAdviceGiven(self):
        """When an advice is given, it is versioned and relevant item infos are saved.
           Moreover, advice is only versioned if it was modified."""
        cfg = self.meetingConfig
        # item data are saved if cfg.historizeItemDataWhenAdviceIsGiven
        self.assertTrue(cfg.getHistorizeItemDataWhenAdviceIsGiven())
        # make sure we know what item rich text fields are enabled
        cfg.setUsedItemAttributes(('description', 'detailedDescription', 'motivation', ))
        cfg.setItemAdviceStates([self._stateMappingFor('proposed'), ])
        cfg.setItemAdviceEditStates([self._stateMappingFor('proposed'), ])
        cfg.setItemAdviceViewStates([self._stateMappingFor('proposed'), ])
        # set that default value of field 'advice_hide_during_redaction' will be True
        cfg.setDefaultAdviceHiddenDuringRedaction(['meetingadvice'])
        self.changeUser('pmCreator1')
        # create an item and ask the advice of group 'vendors'
        data = {
            'title': 'Item to advice',
            'category': 'maintenance',
            'optionalAdvisers': (self.vendors_uid, self.developers_uid, ),
            'description': '<p>Item description</p>',
        }
        item = self.create('MeetingItem', **data)
        item.setDetailedDescription('<p>Item detailed description</p>')
        item.setMotivation('<p>Item motivation</p>')
        item.setDecision('<p>Item decision</p>')
        self.proposeItem(item)
        # give advice
        self.changeUser('pmReviewer2')
        advice = createContentInContainer(item,
                                          'meetingadvice',
                                          **{'advice_group': self.vendors_uid,
                                             'advice_type': u'negative',
                                             'advice_hide_during_redaction': False,
                                             'advice_comment': RichTextValue(u'My comment')})
        # advice is versioned when it is given, aka transition giveAdvice has been triggered
        pr = api.portal.get_tool('portal_repository')
        self.assertFalse(pr.getHistoryMetadata(advice))
        self.changeUser('pmReviewer1')
        self.validateItem(item)
        h_metadata = pr.getHistoryMetadata(advice)
        self.assertTrue(h_metadata)
        # first version, item data was historized on it
        self.assertEquals(h_metadata._available, [0])
        previous = pr.retrieve(advice, 0).object
        self.assertEquals(previous.historized_item_data,
                          [{'field_name': 'title', 'field_content': 'Item to advice'},
                           {'field_name': 'description', 'field_content': '<p>Item description</p>'},
                           {'field_name': 'detailedDescription', 'field_content': '<p>Item detailed description</p>'},
                           {'field_name': 'motivation', 'field_content': '<p>Item motivation</p>'},
                           {'field_name': 'decision', 'field_content': '<p>Item decision</p>'}])
        # when giving advice for a second time, if advice is not edited, it is not versioned uselessly
        self.backToState(item, self._stateMappingFor('proposed'))
        self.assertEquals(advice.queryState(), 'advice_under_edit')
        self.validateItem(item)
        self.assertEquals(advice.queryState(), 'advice_given')
        h_metadata = pr.getHistoryMetadata(advice)
        self.assertEquals(h_metadata._available, [0])

        # come back to 'proposed' and edit advice
        item.setDecision('<p>Another decision</p>')
        self.backToState(item, self._stateMappingFor('proposed'))
        notify(ObjectModifiedEvent(advice))
        self.validateItem(item)
        h_metadata = pr.getHistoryMetadata(advice)
        self.assertEquals(h_metadata._available, [0, 1])
        previous = pr.retrieve(advice, 1).object
        # xxx Namur, decision is empty before presentation of item in meeting
        self.assertEquals(previous.historized_item_data,
                          [{'field_name': 'title', 'field_content': 'Item to advice'},
                           {'field_name': 'description', 'field_content': '<p>Item description</p>'},
                           {'field_name': 'detailedDescription', 'field_content': '<p>Item detailed description</p>'},
                           {'field_name': 'motivation', 'field_content': '<p>Item motivation</p>'},
                           {'field_name': 'decision', 'field_content': '<p>Item description</p>'}])

    def _checkDelayStartedStoppedOn(self):
        # make advice giveable when item is 'validated'
        cfg = self.meetingConfig
        cfg.setItemAdviceStates(('validated', ))
        cfg.setItemAdviceEditStates(('validated', ))
        self.changeUser('pmManager')
        # configure one automatic adviser with delay
        # and ask one non-delay-aware optional adviser
        cfg.setCustomAdvisers(
            [{'row_id': 'unique_id_123',
              'org': self.developers_uid,
              'gives_auto_advice_on': 'not:item/getBudgetRelated',
              'for_item_created_from': '2012/01/01',
              'for_item_created_until': '',
              'delay': '5',
              'delay_label': ''}, ])
        data = {
            'title': 'Item to advice',
            'category': 'maintenance'
        }
        item = self.create('MeetingItem', **data)
        item.setOptionalAdvisers((self.vendors_uid, ))
        item._update_after_edit()
        # advice are correctly asked
        self.assertEquals(
            sorted(item.adviceIndex.keys()),
            sorted([self.vendors_uid, self.developers_uid]))
        # for now, dates are not defined
        self.assertEquals([advice['delay_started_on'] for advice in item.adviceIndex.values()],
                          [None, None])
        self.assertEquals([advice['delay_stopped_on'] for advice in item.adviceIndex.values()],
                          [None, None])
        # propose the item, nothing should have changed
        self.proposeItem(item)
        self.assertEqual(
            sorted(item.adviceIndex.keys()),
            sorted([self.vendors_uid, self.developers_uid]))
        self.assertEqual(
            [advice['delay_started_on'] for advice in item.adviceIndex.values()],
            [None, None])
        self.assertEqual(
            [advice['delay_stopped_on'] for advice in item.adviceIndex.values()],
            [None, None])
        # now do delays start
        # delay will start when the item advices will be giveable
        # advices are giveable when item is validated, so validate the item
        # this will initialize the 'delay_started_on' date
        self.validateItem(item)
        self.assertEqual(item.queryState(), self._stateMappingFor('validated'))
        # we have datetime now in 'delay_started_on' and still nothing in 'delay_stopped_on'
        self.assertTrue(isinstance(item.adviceIndex[self.developers_uid]['delay_started_on'], datetime))
        self.assertTrue(item.adviceIndex[self.developers_uid]['delay_stopped_on'] is None)
        # vendors optional advice is not delay-aware
        self.assertTrue(item.adviceIndex[self.vendors_uid]['delay_started_on'] is None)
        self.assertTrue(item.adviceIndex[self.vendors_uid]['delay_stopped_on'] is None)
        # xxx Namur set item back to proposed, 'delay_stopped_on' not set because for Namur we must return to itemcreated
        self.backToState(item, self.WF_STATE_NAME_MAPPINGS['proposed'])
        self.assertTrue(item.adviceIndex[self.developers_uid]['delay_started_on'] is None)
        self.assertTrue(item.adviceIndex[self.developers_uid]['delay_stopped_on'] is None)
        # vendors optional advice is not delay-aware
        self.assertTrue(item.adviceIndex[self.vendors_uid]['delay_started_on'] is None)
        self.assertTrue(item.adviceIndex[self.vendors_uid]['delay_stopped_on'] is None)
        self.validateItem(item)

        # if we go on, the 'delay_started_on' date does not change anymore, even in a state where
        # advice are not giveable anymore, but at this point, the 'delay_stopped_date' will be set.
        # We present the item
        self.create('Meeting', date=DateTime('2012/01/01'))
        saved_developers_start_date = item.adviceIndex[self.developers_uid]['delay_started_on']
        saved_vendors_start_date = item.adviceIndex[self.vendors_uid]['delay_started_on']
        self.presentItem(item)
        self.assertEqual(item.queryState(), self._stateMappingFor('presented'))
        self.assertEqual(item.adviceIndex[self.developers_uid]['delay_started_on'], saved_developers_start_date)
        self.assertEqual(item.adviceIndex[self.vendors_uid]['delay_started_on'], saved_vendors_start_date)
        # the 'delay_stopped_on' is now set on the delay-aware advice
        self.assertTrue(isinstance(item.adviceIndex[self.developers_uid]['delay_stopped_on'], datetime))
        self.assertTrue(item.adviceIndex[self.vendors_uid]['delay_stopped_on'] is None)
        # if we excute the transition that will reinitialize dates, it is 'backToItemCreated'
        self.assertEqual(cfg.getTransitionsReinitializingDelays(),
                         (self._transitionMappingFor('backToItemCreated'), ))
        self.backToState(item, self._stateMappingFor('itemcreated'))
        self.assertEqual(item.queryState(), self._stateMappingFor('itemcreated'))
        # the delays have been reinitialized to None
        self.assertEqual([advice['delay_started_on'] for advice in item.adviceIndex.values()],
                         [None, None])
        self.assertEqual([advice['delay_stopped_on'] for advice in item.adviceIndex.values()],
                         [None, None])

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
