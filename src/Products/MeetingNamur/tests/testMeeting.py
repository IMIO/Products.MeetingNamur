# -*- coding: utf-8 -*-
#
# File: testMeeting.py
#
# Copyright (c) 2007-2010 by PloneGov
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

from DateTime import DateTime
from Products.MeetingCommunes.tests.testMeeting import testMeetingType as mctm
from Products.MeetingNamur.tests.MeetingNamurTestCase import MeetingNamurTestCase


class testMeeting(MeetingNamurTestCase, mctm):
    """
        Tests the Meeting class methods.
    """

    def test_pm_RemoveOrDeleteLinkedItem(self):
        """
            Give temporary manager right to pmManager.
        """
        self.portal.acl_users.portal_role_manager.assignRoleToPrincipal('Manager', 'pmManager')
        mctm.test_pm_RemoveOrDeleteLinkedItem(self)


    def test_pm_InsertItemOnItemDecisionFirstWords(self):
        """Test when inserting item in a meeting using
           'on_item_decision_first_words' insertion method."""
        cfg = self.meetingConfig
        cfg.setInsertingMethodsOnAddItem(({'insertingMethod': 'on_item_decision_first_words', 'reverse': '0'}, ))
        self.changeUser('pmManager')
        meeting = self.create('Meeting', date=DateTime('2019/09/20').asdatetime())
        # xxx Namur, creator place decision in description field and it's copied on decision field when the item is validate
        data = ({'description': "<p>DÉCIDE d'engager Madame Untell Anne au poste proposé</p>"},
                {'description': "<p>DÉCIDE de refuser</p>"},
                {'description': "<p>REFUSE d'engager Madame Untell Anne au poste proposé</p>"},
                {'description': "<p>A REFUSÉ d'engager Madame Untell Anne au poste proposé</p>"},
                {'description': "<p>DECIDE aussi de ne pas décider</p>"},
                {'description': "<p>ACCEPTE d'engager Madame Untell Anne au poste proposé</p>"},
                {'description': "<p>ACCEPTENT d'engager Madame Untell Anne au poste proposé</p>"}, )
        for itemData in data:
            item = self.create('MeetingItem', **itemData)
            self.presentItem(item)
        self.assertEqual(
            [anItem.getDecision() for anItem in meeting.get_items(ordered=True)],
            ["<p>A REFUS\xc3\x89 d'engager Madame Untell Anne au poste propos\xc3\xa9</p>",
             "<p>ACCEPTE d'engager Madame Untell Anne au poste propos\xc3\xa9</p>",
             "<p>ACCEPTENT d'engager Madame Untell Anne au poste propos\xc3\xa9</p>",
             '<p>DECIDE aussi de ne pas d\xc3\xa9cider</p>',
             "<p>D\xc3\x89CIDE d'engager Madame Untell Anne au poste propos\xc3\xa9</p>",
             '<p>D\xc3\x89CIDE de refuser</p>',
             "<p>REFUSE d'engager Madame Untell Anne au poste propos\xc3\xa9</p>",
             '<p>This is the first recurring item.</p>',
             '<p>This is the second recurring item.</p>'])
        self.assertEqual(
            [anItem._findOrderFor('on_item_decision_first_words') for anItem in meeting.get_items(ordered=True)],
            [u"a refuse d'engager madame untell",
             u"accepte d'engager madame untell anne",
             u"acceptent d'engager madame untell anne",
             u'decide aussi de ne pas',
             u"decide d'engager madame untell anne",
             u'decide de refuser',
             u"refuse d'engager madame untell anne",
             u'this is the first recurring',
             u'this is the second recurring'])


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testMeeting, prefix='test_pm_'))
    return suite
