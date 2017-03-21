# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 by Imio.be
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
from Products.PloneMeeting.tests.helpers import PloneMeetingTestingHelpers


class MeetingNamurTestingHelpers(PloneMeetingTestingHelpers):
    '''Override some values of PloneMeetingTestingHelpers.'''

    TRANSITIONS_FOR_PROPOSING_ITEM_1 = ('propose',)
    TRANSITIONS_FOR_PROPOSING_ITEM_2 = ('propose',)
    TRANSITIONS_FOR_VALIDATING_ITEM_1 = ('propose',
                                         'validate',)
    TRANSITIONS_FOR_VALIDATING_ITEM_2 = ('propose',
                                         'validate',)
    TRANSITIONS_FOR_PRESENTING_ITEM_1 = ('propose', 'validate', 'present',)
    TRANSITIONS_FOR_PRESENTING_ITEM_2 = ('propose', 'validate', 'present',)
    TRANSITIONS_FOR_ACCEPTING_ITEMS_1 = ('freeze', 'decide',)
    TRANSITIONS_FOR_ACCEPTING_ITEMS_2 = ('freeze', 'publish', 'decide',)

    TRANSITIONS_FOR_DECIDING_MEETING_1 = ('freeze', 'decide',)
    TRANSITIONS_FOR_DECIDING_MEETING_2 = ('freeze', 'publish', 'decide',)
    TRANSITIONS_FOR_CLOSING_MEETING_1 = ('freeze', 'decide', 'close',)
    TRANSITIONS_FOR_CLOSING_MEETING_2 = ('freeze', 'publish', 'decide', 'close',)
    BACK_TO_WF_PATH_1 = {
        # Meeting
        'created': ('backToDecided',
                    'backToFrozen',
                    'backToCreated',),
        # MeetingItem
        'itemcreated': ('backToItemFrozen',
                        'backToPresented',
                        'backToValidated',
                        'backToItemCreated',),
        'proposed': ('backToItemFrozen',
                     'backToPresented',
                     'backToValidated',
                     'backToItemCreated',
                     'propose',),
        'validated': ('backToItemFrozen',
                      'backToPresented',
                      'backToValidated',)}
    BACK_TO_WF_PATH_2 = {
        # Meeting
        'created': ('backToDecided',
                    'backToPublished',
                    'backToFrozen',
                    'backToCreated',),
        # MeetingItem
        'itemcreated': ('backToItemPublished',
                        'backToItemFrozen',
                        'backToPresented',
                        'backToValidated',
                        'backToProposed',
                        'backToItemCreated',),
        'proposed': ('backToItemPublished',
                     'backToItemFrozen',
                     'backToPresented',
                     'backToValidated',
                     'backToProposed',),
        'validated': ('backToItemPublished',
                      'backToItemFrozen',
                      'backToPresented',
                      'backToValidated',)}

    WF_STATE_NAME_MAPPINGS = {'itemcreated': 'itemcreated',
                              'proposed': 'proposed',
                              'validated': 'validated',
                              'presented': 'presented'}

    # in which state an item must be after an particular meeting transition?
    ITEM_WF_STATE_AFTER_MEETING_TRANSITION = {'publish_decisions': 'accepted',
                                              'close': 'accepted'}

    TRANSITIONS_FOR_ACCEPTING_ITEMS_MEETING_1 = TRANSITIONS_FOR_ACCEPTING_ITEMS_MEETING_2 = ('freeze', 'decide', )

    def _createMeetingWithItems(self, withItems=True, meetingDate=DateTime()):
        '''Create a meeting with a bunch of items.
           Overrided to do it as 'Manager' to be able
           to add recurring items.'''
        from plone.app.testing.helpers import setRoles
        currentMember = self.portal.portal_membership.getAuthenticatedMember()
        currentMemberRoles = currentMember.getRoles()
        setRoles(self.portal, currentMember.getId(), currentMemberRoles + ['Manager', ])
        meeting = PloneMeetingTestingHelpers._createMeetingWithItems(self,
                                                                        withItems=withItems,
                                                                        meetingDate=meetingDate)
        setRoles(self.portal, currentMember.getId(), currentMemberRoles)
        return meeting
