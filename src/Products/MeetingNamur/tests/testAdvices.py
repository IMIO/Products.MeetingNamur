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

from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase
from Products.MeetingCommunes.tests.testAdvices import testAdvices as mcta
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer


class testAdvices(MeetingNamurTestCase, mcta):
    '''Tests various aspects of advices management.
       Advices are enabled for PloneGov Assembly, not for PloneMeeting Assembly.'''

    def test_subproduct_call_MayTriggerGiveAdviceWhenItemIsBackToANotViewableState(self, ):
        '''Run the test_pm_MayTriggerGiveAdviceWhenItemIsBackToANotViewableState from PloneMeeting.'''
        '''Test that if an item is set back to a state the user that set it back can
           not view anymore, and that the advice turn from giveable to not giveable anymore,
           transitions triggered on advice that will 'giveAdvice'.'''
        # advice can be given when item is validated
        self.meetingConfig.setItemAdviceStates((self.WF_STATE_NAME_MAPPINGS['validated'], ))
        self.meetingConfig.setItemAdviceEditStates((self.WF_STATE_NAME_MAPPINGS['validated'], ))
        self.meetingConfig.setItemAdviceViewStates((self.WF_STATE_NAME_MAPPINGS['validated'], ))
        # create an item as vendors and give an advice as vendors on it
        # it is viewable by MeetingManager when validated
        self.changeUser('pmCreator2')
        item = self.create('MeetingItem')
        item.setOptionalAdvisers(('vendors', ))
        # validate the item and advice it
        self.validateItem(item)
        self.changeUser('pmReviewer2')
        createContentInContainer(item,
                                 'meetingadvice',
                                 **{'advice_group': 'vendors',
                                    'advice_type': u'positive',
                                    'advice_comment': RichTextValue(u'My comment')})
        # make sure if a MeetingManager send the item back to 'created' it works...
        self.changeUser('pmManager')
        # do the back transition that send the item back to 'created'
        # this will work...
        self.do(item, 'backToItemCreated')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testAdvices, prefix='test_subproduct_'))
    return suite
