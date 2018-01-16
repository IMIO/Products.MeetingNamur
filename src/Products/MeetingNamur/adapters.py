# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Copyright (c) 2017 by Imio.be
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
# You should have received a copy of the GNU General Public LicensePloneMeeting: Read budget infos
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# ------------------------------------------------------------------------------

from AccessControl import ClassSecurityInfo
from collections import OrderedDict
from Globals import InitializeClass
from zope.interface import implements
from zope.i18n import translate

from Products.CMFCore.permissions import ReviewPortalContent
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.atapi import DisplayList
from plone import api

from imio.helpers.xhtml import xhtmlContentIsEmpty
from Products.PloneMeeting.adapters import ItemPrettyLinkAdapter
from Products.PloneMeeting.interfaces import IMeetingCustom
from Products.PloneMeeting.interfaces import IMeetingItemCustom
from Products.PloneMeeting.interfaces import IMeetingGroupCustom
from Products.PloneMeeting.interfaces import IMeetingConfigCustom
from Products.PloneMeeting.interfaces import IToolPloneMeetingCustom
from Products.PloneMeeting.Meeting import Meeting
from Products.PloneMeeting.Meeting import MeetingWorkflowActions
from Products.PloneMeeting.Meeting import MeetingWorkflowConditions
from Products.PloneMeeting.MeetingConfig import MeetingConfig
from Products.PloneMeeting.MeetingGroup import MeetingGroup
from Products.PloneMeeting.MeetingItem import MeetingItem
from Products.PloneMeeting.MeetingItem import MeetingItemWorkflowActions
from Products.PloneMeeting.MeetingItem import MeetingItemWorkflowConditions
from Products.PloneMeeting.model import adaptations
from Products.PloneMeeting.ToolPloneMeeting import ToolPloneMeeting
from Products.PloneMeeting.utils import sendMail
from Products.PloneMeeting.utils import sendMailIfRelevant

from Products.MeetingNamur import logger
from Products.MeetingNamur.config import FINANCE_ADVICES_COLLECTION_ID
from Products.MeetingNamur.interfaces import IMeetingItemNamurWorkflowConditions
from Products.MeetingNamur.interfaces import IMeetingItemNamurWorkflowActions
from Products.MeetingNamur.interfaces import IMeetingNamurWorkflowConditions
from Products.MeetingNamur.interfaces import IMeetingNamurWorkflowActions
from Products.MeetingNamur.interfaces import IMeetingItemNamurCollegeWorkflowConditions
from Products.MeetingNamur.interfaces import IMeetingItemNamurCollegeWorkflowActions
from Products.MeetingNamur.interfaces import IMeetingNamurCollegeWorkflowConditions
from Products.MeetingNamur.interfaces import IMeetingNamurCollegeWorkflowActions
from Products.MeetingNamur.interfaces import IMeetingItemNamurCouncilWorkflowConditions
from Products.MeetingNamur.interfaces import IMeetingItemNamurCouncilWorkflowActions
from Products.MeetingNamur.interfaces import IMeetingNamurCouncilWorkflowConditions
from Products.MeetingNamur.interfaces import IMeetingNamurCouncilWorkflowActions
# Names of available workflow adaptations.
customWfAdaptations = ('return_to_proposing_group', 'return_to_proposing_group_with_last_validation',
                       'return_to_proposing_group_with_all_validations')
MeetingConfig.wfAdaptations = customWfAdaptations
originalPerformWorkflowAdaptations = adaptations.performWorkflowAdaptations

RETURN_TO_PROPOSING_GROUP_CUSTOM_PERMISSIONS = {'meetingitemnamur_workflow':
    # view permissions
    {'Access contents information':
    ('Manager', 'MeetingManager', 'MeetingMember', 'MeetingTaxController',
     'MeetingReviewer', 'MeetingObserverLocal', 'Reader', ),
    'View':
    ('Manager', 'MeetingManager', 'MeetingMember', 'MeetingTaxController',
     'MeetingReviewer', 'MeetingObserverLocal', 'Reader', ),
    'PloneMeeting: Read decision':
    ('Manager', 'MeetingManager', 'MeetingMember', 'MeetingTaxController',
     'MeetingReviewer', 'MeetingObserverLocal', 'Reader', ),
    'PloneMeeting: Read item observations':
    ('Manager', 'MeetingManager', 'MeetingMember', 'MeetingTaxController',
     'MeetingReviewer', 'MeetingObserverLocal', 'Reader', ),
    'PloneMeeting: Read budget infos':
    ('Manager', 'MeetingManager', 'MeetingMember', 'MeetingTaxController',
     'MeetingReviewer', 'MeetingObserverLocal', 'Reader', ),
    # edit permissions
    'Modify portal content':
    ('Manager', 'MeetingMember',  'MeetingManager',  'MeetingReviewer', ),
    'PloneMeeting: Write decision':
    ('Manager', ),
    'Review portal content':
    ('Manager', 'MeetingMember',  'MeetingManager',  'MeetingReviewer', ),
    'Add portal content':
    ('Manager', 'MeetingMember',  'MeetingManager',  'MeetingReviewer', ),
    'PloneMeeting: Add annex':
    ('Manager', 'MeetingMember',  'MeetingManager',  'MeetingReviewer', ),
    'PloneMeeting: Add annexDecision':
    ('Manager', 'MeetingMember',  'MeetingManager',  'MeetingReviewer', ),
    'PloneMeeting: Write budget infos':
    ('Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingBudgetImpactEditor', 'MeetingManager',
     'MeetingBudgetImpactReviewer', ),
    'MeetingNamur: Write description':
    ('Manager', 'MeetingMember', 'MeetingManager', 'MeetingReviewer',),
    # MeetingManagers edit permissions
    'MeetingNamur: Write certified signatures':
    ('Manager',),
    'PloneMeeting: Write marginal notes':
    ('Manager',),
    'PloneMeeting: Write item MeetingManager reserved fields':
    ('Manager', 'MeetingManager',),
    'Delete objects':
    ['Manager', ],}
}

adaptations.RETURN_TO_PROPOSING_GROUP_CUSTOM_PERMISSIONS = RETURN_TO_PROPOSING_GROUP_CUSTOM_PERMISSIONS

RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE = {'meetingitemnamur_workflow': 'meetingitemnamur_workflow.itemcreated'}

adaptations.RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE = RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE


class CustomMeeting(Meeting):
    '''Adapter that adapts a meeting implementing IMeeting to the
       interface IMeetingCustom.'''

    implements(IMeetingCustom)
    security = ClassSecurityInfo()

    def __init__(self, meeting):
        self.context = meeting

    # Implements here methods that will be used by templates
    security.declarePublic('getPrintableItems')

    def getPrintableItems(self, itemUids, listTypes=['normal'], ignore_review_states=[],
                          privacy='*', oralQuestion='both', toDiscuss='both', categories=[],
                          excludedCategories=[], groupIds=[], excludedGroupIds=[],
                          firstNumber=1, renumber=False):
        '''Returns a list of items.
           An extra list of review states to ignore can be defined.
           A privacy can also be given, and the fact that the item is an
           oralQuestion or not (or both). Idem with toDiscuss.
           Some specific categories can be given or some categories to exclude.
           We can also receive in p_groupIds MeetingGroup ids to take into account.
           These 2 parameters are exclusive.  If renumber is True, a list of tuple
           will be return with first element the number and second element, the item.
           In this case, the firstNumber value can be used.'''
        # We just filter ignore_review_states here and privacy and call
        # getItems(uids), passing the correct uids and removing empty uids.
        # privacy can be '*' or 'public' or 'secret' or 'public_heading' or 'secret_heading'
        # oralQuestion can be 'both' or False or True
        # toDiscuss can be 'both' or 'False' or 'True'
        for elt in itemUids:
            if elt == '':
                itemUids.remove(elt)

        # check filters
        filteredItemUids = []
        uid_catalog = self.context.uid_catalog
        for itemUid in itemUids:
            obj = uid_catalog(UID=itemUid)[0].getObject()
            if obj.queryState() in ignore_review_states:
                continue
            elif not (privacy == '*' or obj.getPrivacy() == privacy):
                continue
            elif not (oralQuestion == 'both' or obj.getOralQuestion() == oralQuestion):
                continue
            elif not (toDiscuss == 'both' or obj.getToDiscuss() == toDiscuss):
                continue
            elif categories and not obj.getCategory() in categories:
                continue
            elif groupIds and not obj.getProposingGroup() in groupIds:
                continue
            elif excludedCategories and obj.getCategory() in excludedCategories:
                continue
            elif excludedGroupIds and obj.getProposingGroup() in excludedGroupIds:
                continue
            filteredItemUids.append(itemUid)
        # in case we do not have anything, we return an empty list
        if not filteredItemUids:
            return []
        else:
            items = self.context.getItems(uids=filteredItemUids, listTypes=listTypes, ordered=True)
            if renumber:
                # return a list of tuple with first element the number and second
                # element the item itself
                i = firstNumber
                res = []
                for item in items:
                    res.append((i, item))
                    i = i + 1
                items = res
            return items

    def _getAcronymPrefix(self, group, groupPrefixes):
        '''This method returns the prefix of the p_group's acronym among all
           prefixes listed in p_groupPrefixes. If group acronym does not have a
           prefix listed in groupPrefixes, this method returns None.'''
        res = None
        groupAcronym = group.getAcronym()
        for prefix in groupPrefixes.iterkeys():
            if groupAcronym.startswith(prefix):
                res = prefix
                break
        return res

    def _getGroupIndex(self, group, groups, groupPrefixes):
        '''Is p_group among the list of p_groups? If p_group is not among
           p_groups but another group having the same prefix as p_group
           (the list of prefixes is given by p_groupPrefixes), we must conclude
           that p_group is among p_groups. res is -1 if p_group is not
           among p_group; else, the method returns the index of p_group in
           p_groups.'''
        prefix = self._getAcronymPrefix(group, groupPrefixes)
        if not prefix:
            if group not in groups:
                return -1
            else:
                return groups.index(group)
        else:
            for gp in groups:
                if gp.getAcronym().startswith(prefix):
                    return groups.index(gp)
            return -1

    def _insertGroupInCategory(self, categoryList, meetingGroup, groupPrefixes, groups, item=None):
        '''Inserts a group list corresponding to p_meetingGroup in the given
           p_categoryList, following meeting group order as defined in the
           main configuration (groups from the config are in p_groups).
           If p_item is specified, the item is appended to the group list.'''
        usedGroups = [g[0] for g in categoryList[1:]]
        groupIndex = self._getGroupIndex(meetingGroup, usedGroups, groupPrefixes)
        if groupIndex == -1:
            # Insert the group among used groups at the right place.
            groupInserted = False
            i = -1
            for usedGroup in usedGroups:
                i += 1
                if groups.index(meetingGroup) < groups.index(usedGroup):
                    if item:
                        categoryList.insert(i + 1, [meetingGroup, item])
                    else:
                        categoryList.insert(i + 1, [meetingGroup])
                    groupInserted = True
                    break
            if not groupInserted:
                if item:
                    categoryList.append([meetingGroup, item])
                else:
                    categoryList.append([meetingGroup])
        else:
            # Insert the item into the existing group.
            if item:
                categoryList[groupIndex + 1].append(item)

    def _insertItemInCategory(self, categoryList, item, byProposingGroup, groupPrefixes, groups):
        '''This method is used by the next one for inserting an item into the
           list of all items of a given category. if p_byProposingGroup is True,
           we must add it in a sub-list containing items of a given proposing
           group. Else, we simply append it to p_category.'''
        if not byProposingGroup:
            categoryList.append(item)
        else:
            group = item.getProposingGroup(True)
            self._insertGroupInCategory(categoryList, group, groupPrefixes, groups, item)

    security.declarePublic('getPrintableItemsByCategory')

    def getPrintableItemsByCategory(self, itemUids=[], listTypes=['normal'],
                                    ignore_review_states=[], by_proposing_group=False, group_prefixes={},
                                    privacy='*', oralQuestion='both', toDiscuss='both', categories=[],
                                    excludedCategories=[], groupIds=[], excludedGroupIds=[],
                                    firstNumber=1, renumber=False,
                                    includeEmptyCategories=False, includeEmptyGroups=False,
                                    forceCategOrderFromConfig=False, allNoConfidentialItems=False):
        '''Returns a list of (late or normal or both) items (depending on p_listTypes)
           ordered by category. Items being in a state whose name is in
           p_ignore_review_state will not be included in the result.
           If p_by_proposing_group is True, items are grouped by proposing group
           within every category. In this case, specifying p_group_prefixes will
           allow to consider all groups whose acronym starts with a prefix from
           this param prefix as a unique group. p_group_prefixes is a dict whose
           keys are prefixes and whose values are names of the logical big
           groups. A privacy,A toDiscuss and oralQuestion can also be given, the item is a
           toDiscuss (oralQuestion) or not (or both) item.
           If p_forceCategOrderFromConfig is True, the categories order will be
           the one in the config and not the one from the meeting.
           If p_groupIds are given, we will only consider these proposingGroups.
           If p_includeEmptyCategories is True, categories for which no
           item is defined are included nevertheless. If p_includeEmptyGroups
           is True, proposing groups for which no item is defined are included
           nevertheless.Some specific categories can be given or some categories to exclude.
           These 2 parameters are exclusive.  If renumber is True, a list of tuple
           will be return with first element the number and second element, the item.
           In this case, the firstNumber value can be used.'''
        # The result is a list of lists, where every inner list contains:
        # - at position 0: the category object (MeetingCategory or MeetingGroup)
        # - at position 1 to n: the items in this category
        # If by_proposing_group is True, the structure is more complex.
        # listTypes is a list that can be filled with 'normal' and/or 'late'
        # oralQuestion can be 'both' or False or True
        # toDiscuss can be 'both' or 'False' or 'True'
        # privacy can be '*' or 'public' or 'secret'
        # Every inner list contains:
        # - at position 0: the category object
        # - at positions 1 to n: inner lists that contain:
        #   * at position 0: the proposing group object
        #   * at positions 1 to n: the items belonging to this group.
        def _comp(v1, v2):
            if v1[0].getOrder(onlySelectable=False) < v2[0].getOrder(onlySelectable=False):
                return -1
            elif v1[0].getOrder(onlySelectable=False) > v2[0].getOrder(onlySelectable=False):
                return 1
            else:
                return 0
        res = []
        items = []
        previousCatId = None
        tool = getToolByName(self.context, 'portal_plonemeeting')
        # Retrieve the list of items
        for elt in itemUids:
            if elt == '':
                itemUids.remove(elt)

        items = self.context.getItems(uids=itemUids, listTypes=listTypes, ordered=True)

        if by_proposing_group:
            groups = tool.getMeetingGroups()
        else:
            groups = None
        if items:
            for item in items:
                # Check if the review_state has to be taken into account
                if item.queryState() in ignore_review_states:
                    continue
                elif not (privacy == '*' or item.getPrivacy() == privacy):
                    continue
                elif not (oralQuestion == 'both' or item.getOralQuestion() == oralQuestion):
                    continue
                elif not (toDiscuss == 'both' or item.getToDiscuss() == toDiscuss):
                    continue
                elif groupIds and not item.getProposingGroup() in groupIds:
                    continue
                elif categories and not item.getCategory() in categories:
                    continue
                elif excludedCategories and item.getCategory() in excludedCategories:
                    continue
                elif excludedGroupIds and item.getProposingGroup() in excludedGroupIds:
                    continue
                elif allNoConfidentialItems:
                    user = self.context.portal_membership.getAuthenticatedMember()
                    userCanView = user.has_permission('View', item)
                    if item.getIsConfidentialItem() and not userCanView:
                        continue
                currentCat = item.getCategory(theObject=True)
                # Add the item to a new category, excepted if the category already exists.
                catExists = False
                for catList in res:
                    if catList[0] == currentCat:
                        catExists = True
                        break
                # Add the item to a new category, excepted if the category already exists.
                if catExists:
                    self._insertItemInCategory(catList, item,
                                               by_proposing_group, group_prefixes, groups)
                else:
                    res.append([currentCat])
                    self._insertItemInCategory(res[-1], item,
                                               by_proposing_group, group_prefixes, groups)
        if forceCategOrderFromConfig or cmp(listTypes.sort(), ['late', 'normal']) == 0:
            res.sort(cmp=_comp)
        if includeEmptyCategories:
            meetingConfig = tool.getMeetingConfig(
                self.context)
            # onlySelectable = False will also return disabled categories...
            allCategories = [cat for cat in meetingConfig.getCategories(onlySelectable=False)
                             if api.content.get_state(cat) == 'active']
            usedCategories = [elem[0] for elem in res]
            for cat in allCategories:
                if cat not in usedCategories:
                    # no empty service, we want only show department
                    if cat.getAcronym().find('-') > 0:
                        continue
                    else:
                        # no empty department
                        dpt_empty = True
                        for uc in usedCategories:
                            if uc.getAcronym().startswith(cat.getAcronym()):
                                dpt_empty = False
                                break
                        if dpt_empty:
                            continue
                    # Insert the category among used categories at the right place.
                    categoryInserted = False
                    i = 0
                    for obj in res:
                        try:
                            if not obj[0].getAcronym().startswith(cat.getAcronym()):
                                i = i + 1
                                continue
                            else:
                                usedCategories.insert(i, cat)
                                res.insert(i, [cat])
                                categoryInserted = True
                                break
                        except:
                            continue
                    if not categoryInserted:
                        usedCategories.append(cat)
                        res.append([cat])
        if by_proposing_group and includeEmptyGroups:
            # Include, in every category list, not already used groups.
            # But first, compute "macro-groups": we will put one group for
            # every existing macro-group.
            macroGroups = []  # Contains only 1 group of every "macro-group"
            consumedPrefixes = []
            for group in groups:
                prefix = self._getAcronymPrefix(group, group_prefixes)
                if not prefix:
                    group._v_printableName = group.Title()
                    macroGroups.append(group)
                else:
                    if prefix not in consumedPrefixes:
                        consumedPrefixes.append(prefix)
                        group._v_printableName = group_prefixes[prefix]
                        macroGroups.append(group)
            # Every category must have one group from every macro-group
            for catInfo in res:
                for group in macroGroups:
                    self._insertGroupInCategory(catInfo, group, group_prefixes,
                                                groups)
                    # The method does nothing if the group (or another from the
                    # same macro-group) is already there.
        if renumber:
            # return a list of tuple with first element the number and second
            # element the item itself
            i = firstNumber
            res = []
            for item in items:
                res.append((i, item))
                i = i + 1
            items = res
        return res

    security.declarePublic('getNumberOfItems')

    def getNumberOfItems(self, itemUids, privacy='*', categories=[], listTypes=['normal']):
        '''Returns the number of items depending on parameters.
           This is used in templates to know how many items of a particular kind exist and
           often used to determine the 'firstNumber' parameter of getPrintableItems/getPrintableItemsByCategory.'''
        # sometimes, some empty elements are inserted in itemUids, remove them...
        itemUids = [itemUid for itemUid in itemUids if itemUid != '']
        if not categories and privacy == '*':
            return len(self.context.getItems(uids=itemUids, listTypes=listTypes))
        # Either, we will have to filter (privacy, categories, late)
        filteredItemUids = []
        uid_catalog = getToolByName(self.context, 'uid_catalog')
        for itemUid in itemUids:
            obj = uid_catalog(UID=itemUid)[0].getObject()
            if not (privacy == '*' or obj.getPrivacy() == privacy):
                continue
            elif not (categories == [] or obj.getCategory() in categories):
                continue
            elif not obj.isLate() == bool(listTypes == ['late']):
                continue
            filteredItemUids.append(itemUid)
        return len(filteredItemUids)

    security.declarePublic('getPrintableItemsByNumCategory')

    def getPrintableItemsByNumCategory(self, listTypes=['normal'], uids=[],
                                       catstoexclude=[], exclude=True, allItems=False):
        '''Returns a list of items ordered by category number. If there are many
           items by category, there is always only one category, even if the
           user have chosen a different order. If exclude=True , catstoexclude
           represents the category number that we don't want to print and if
           exclude=False, catsexclude represents the category number that we
           only want to print. This is useful when we want for exemple to
           exclude a personnal category from the meeting an realize a separate
           meeeting for this personal category. If allItems=True, we return
           late items AND items in order.'''
        def getPrintableNumCategory(current_cat):
            '''Method used here above.'''
            current_cat_id = current_cat.getId()
            current_cat_name = current_cat.Title()
            current_cat_name = current_cat_name[0:2]
            try:
                catNum = int(current_cat_name)
            except ValueError:
                current_cat_name = current_cat_name[0:1]
                try:
                    catNum = int(current_cat_name)
                except ValueError:
                    catNum = current_cat_id
            return catNum

        if not allItems and listTypes == ['late']:
            items = self.context.getItems(uids=uids, listTypes=['late'], ordered=True)
        elif not allItems and not listTypes == ['late']:
            items = self.context.getItems(uids=uids, listTypes=['normal'], ordered=True)
        else:
            items = self.context.getItems(uids=uids, ordered=True)
        # res contains all items by category, the key of res is the category
        # number. Pay attention that the category number is obtain by extracting
        # the 2 first caracters of the categoryname, thus the categoryname must
        # be for exemple ' 2.travaux' or '10.Urbanisme. If not, the catnum takes
        # the value of the id + 1000 to be sure to place those categories at the
        # end.
        res = {}
        # First, we create the category and for each category, we create a
        # dictionary that must contain the list of item in in res[catnum][1]
        for item in items:
            if uids:
                if (item.UID() in uids):
                    inuid = "ok"
                else:
                    inuid = "ko"
            else:
                inuid = "ok"
            if (inuid == "ok"):
                current_cat = item.getCategory(theObject=True)
                catNum = getPrintableNumCategory(current_cat)
                if catNum in res:
                    res[catNum][1][item.getItemNumber()] = item
                else:
                    res[catNum] = {}
                    # first value of the list is the category object
                    res[catNum][0] = item.getCategory(True)
                    # second value of the list is a list of items
                    res[catNum][1] = {}
                    res[catNum][1][item.getItemNumber()] = item

        # Now we must sort the res dictionary with the key (containing catnum)
        # and copy it in the returned array.
        reskey = res.keys()
        reskey.sort()
        ressort = []
        for i in reskey:
            if catstoexclude:
                if (i in catstoexclude):
                    if exclude is False:
                        guard = True
                    else:
                        guard = False
                else:
                    if exclude is False:
                        guard = False
                    else:
                        guard = True
            else:
                guard = True

            if guard is True:
                k = 0
                ressorti = []
                ressorti.append(res[i][0])
                resitemkey = res[i][1].keys()
                resitemkey.sort()
                ressorti1 = []
                for j in resitemkey:
                    k = k + 1
                    ressorti1.append([res[i][1][j], k])
                ressorti.append(ressorti1)
                ressort.append(ressorti)
        return ressort

    security.declarePublic('getVotes')

    def getVotes(self):
        '''Get all item with "votes" for a meeting in a list to print in template'''
        res = []
        for item in self.context.getAllItems(ordered=True):
            if item.getVote():
                res.append(item)
        return res


class CustomMeetingItem(MeetingItem):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCustom.'''
    implements(IMeetingItemCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item

    def getFinanceAdviceId(self):
        """ """
        tool = api.portal.get_tool('portal_plonemeeting')
        cfg = tool.getMeetingConfig(self.context)
        usedFinanceGroupIds = cfg.adapted().getUsedFinanceGroupIds(self.context)
        adviserIds = self.context.adviceIndex.keys()
        financeAdvisersIds = set(usedFinanceGroupIds).intersection(set(adviserIds))
        if financeAdvisersIds:
            return list(financeAdvisersIds)[0]
        else:
            return None

    def getEchevinsForProposingGroup(self):
        '''Returns all echevins defined for the proposing group'''
        res = []
        tool = getToolByName(self.context, 'portal_plonemeeting')
        # keep also inactive groups because this method is often used in the customAdviser
        # TAL expression and a disabled MeetingGroup must still be taken into account
        for group in tool.getMeetingGroups(onlyActive=False):
            if self.context.getProposingGroup() in group.getEchevinServices():
                res.append(group.getId())
        return res

    security.declarePublic('listGrpBudgetInfosAdviser')

    def listGrpBudgetInfosAdviser(self):
        '''Returns a list of groups that can be selected on an item to modify budgetInfos field.
        acronym group start with DGF'''
        res = []
        res.append(('', self.utranslate('make_a_choice', domain='PloneMeeting')))
        tool = getToolByName(self, "portal_plonemeeting")
        for group in tool.getMeetingGroups(onlyActive=True):
            if group.acronym.startswith('DGF'):
                res.append((group.id, group.getProperty('title')))
        return DisplayList(tuple(res))
    MeetingItem.listGrpBudgetInfosAdviser = listGrpBudgetInfosAdviser

    security.declarePublic('giveMeetingBudgetImpactReviewerRole')

    def giveMeetingBudgetImpactReviewerRole(self):
        '''Add MeetingBudgetImpactReviewer role when on an item, a group is choosen in BudgetInfosAdviser and state is,
           at least, "presented". Remove role for other grp_budgetimpactreviewers or remove all
           grp_budgetimpactreviewers in local role if state back in state before presented.
        '''
        item = self.getSelf()
        grp_roles = []
        if item.queryState() in ('presented', 'itemfrozen', 'accepted', 'delayed', 'accepted_but_modified',
                                 'pre_accepted', 'refused'):
            #add new MeetingBudgetImpactReviewerRole
            for grpBudgetInfo in item.grpBudgetInfos:
                grp_role = '%s_budgetimpactreviewers' % grpBudgetInfo
                #for each group_budgetimpactreviewers add new local roles
                if grpBudgetInfo:
                    grp_roles.append(grp_role)
                    item.manage_addLocalRoles(grp_role, ('Reader', 'MeetingBudgetImpactReviewer',))
        #suppress old unused group_budgetimpactreviewers
        toRemove = []
        for user, roles in item.get_local_roles():
            if user.endswith('_budgetimpactreviewers') and user not in grp_roles:
                toRemove.append(user)
        item.manage_delLocalRoles(toRemove)

    security.declareProtected('Modify portal content', 'onEdit')

    def onEdit(self, isCreated):
        item = self.getSelf()
        #adapt MeetingBudgetImpactReviewerRole if needed
        item.adapted().giveMeetingBudgetImpactReviewerRole()

    def _initDecisionFieldIfEmpty(self):
        '''
          If decision field is empty, it will be initialized
          with data coming from title and description.
        '''
        # set keepWithNext to False as it will add a 'class' and so
        # xhtmlContentIsEmpty will never consider it empty...
        if xhtmlContentIsEmpty(self.getDecision(keepWithNext=False)):
            self.setDecision("%s" % self.Description())
            self.reindexObject()
    MeetingItem._initDecisionFieldIfEmpty = _initDecisionFieldIfEmpty

    security.declarePublic('customshowDuplicateItemAction')

    def customshowDuplicateItemAction(self):
        '''Condition for displaying the 'duplicate' action in the interface.
           Returns True if the user can duplicate the item.'''
        # Conditions for being able to see the "duplicate an item" action:
        # - the user is creator in some group;
        # - the user must be able to see the item if it is private.
        # The user will duplicate the item in his own folder.
        tool = api.portal.get_tool('portal_plonemeeting')
        item = self.getSelf()
        cfg = tool.getMeetingConfig(self)
        ignoreDuplicateButton = item.queryState() == 'pre_accepted'
        if not cfg.getEnableItemDuplication() or \
                self.isDefinedInTool() or \
                not tool.userIsAmong(['creators']) or \
                not self.adapted().isPrivacyViewable() or ignoreDuplicateButton:
            return False
        return True



    MeetingItem.__pm_old_showDuplicateItemAction = MeetingItem.showDuplicateItemAction
    MeetingItem.showDuplicateItemAction = customshowDuplicateItemAction

    security.declarePublic('getMappingDecision')

    def getMappingDecision(self):
        '''
            In model : list of decisions, we must map some traductions
            accepted : approuved
            removed : removed
            delay : delay
            pre_accepted : /
            accepted_but_modified : Approved with a modification
        '''
        item = self.getSelf()
        state = item.queryState()
        if state == 'accepted_but_modified':
            state = 'approved_but_modified'
        elif state == 'accepted':
            state = 'approved'
        elif state == 'pre_accepted':
            return '/'
        return item.translate(state, domain='plone')

    def adviceDelayIsTimedOutWithRowId(self, groupId, rowIds=[]):
        ''' Check if advice with delay from a certain p_groupId and with
            a row_id contained in p_rowIds is timed out.
        '''
        self = self.getSelf()
        if self.getAdviceDataFor(self) and groupId in self.getAdviceDataFor(self):
            adviceRowId = self.getAdviceDataFor(self, groupId)['row_id']
        else:
            return False

        if not rowIds or adviceRowId in rowIds:
            return self._adviceDelayIsTimedOut(groupId)
        else:
            return False

    security.declarePublic('viewFullFieldInItemEdit')

    def viewFullFieldInItemEdit(self):
        '''
            This method is used in MeetingItem_edit.cpt
        '''
        item = self.getSelf()
        roles = item.portal_membership.getAuthenticatedMember().getRolesInContext(item)
        res = False
        for role in roles:
            if (role == 'Authenticated') or (role == 'Member') or \
                    (role == 'MeetingTaxController') or (role == 'MeetingBudgetImpactReviewer') or \
                    (role == 'MeetingObserverGlobal') or (role == 'Reader'):
                continue
            res = True
            break
        return res

    def getExtraFieldsToCopyWhenCloning(self, cloned_to_same_mc):
        '''
          Keep some new fields when item is cloned (to another mc or from itemtemplate).
        '''
        res = ['grpBudgetInfos', 'itemCertifiedSignatures', 'isConfidentialItem', 'vote']
        if cloned_to_same_mc:
            res = res + []
        return res

class CustomMeetingGroup(MeetingGroup):
    '''Adapter that adapts a meeting group implementing IMeetingGroup to the
       interface IMeetingGroupCustom.'''

    implements(IMeetingGroupCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item

    security.declarePublic('listEchevinServices')

    def listEchevinServices(self):
        '''Returns a list of groups that can be selected on an group (without isEchevin).'''
        res = []
        tool = getToolByName(self, 'portal_plonemeeting')
        # Get every Plone group related to a MeetingGroup
        for group in tool.getMeetingGroups():
            res.append((group.id, group.getProperty('title')))

        return DisplayList(tuple(res))
    MeetingGroup.listEchevinServices = listEchevinServices


    security.declareProtected('Modify portal content', 'onEdit')

    def onEdit(self, isCreated):
        '''Add group_budgetimpactreviewers if DGF group'''
        meeting_group = self.getSelf()
        if meeting_group.acronym.startswith('DGF'):
            groupId = meeting_group.getPloneGroupId('budgetimpactreviewers')
            enc = meeting_group.portal_properties.site_properties.getProperty('default_charset')
            groupTitle = '%s (%s)' % (
                meeting_group.Title().decode(enc),
                meeting_group.utranslate('budgetimpactreviewers', domain='PloneMeeting'))
            meeting_group.portal_groups.addGroup(groupId, title=groupTitle)
            meeting_group.portal_groups.setRolesForGroup(groupId, ('MeetingObserverGlobal',))
            group = meeting_group.portal_groups.getGroupById(groupId)
            group.setProperties(meetingRole='MeetingBudgetImpactReviewer', meetingGroupId=meeting_group.id)


class CustomMeetingConfig(MeetingConfig):
    '''Adapter that adapts a meetingConfig implementing IMeetingConfig to the
       interface IMeetingConfigCustom.'''

    implements(IMeetingConfigCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item

    security.declarePublic('getUsedFinanceGroupIds')

    def getUsedFinanceGroupIds(self, item=None):
        """Possible finance advisers group ids are defined on
           the FINANCE_ADVICES_COLLECTION_ID collection."""
        cfg = self.getSelf()
        tool = api.portal.get_tool('portal_plonemeeting')
        collection = getattr(cfg.searches.searches_items, FINANCE_ADVICES_COLLECTION_ID, None)
        if not collection:
            logger.warn(
                "Method 'getUsedFinanceGroupIds' could not find the '{0}' collection!".format(
                    FINANCE_ADVICES_COLLECTION_ID))
            return []
        # get the indexAdvisers value defined on the collection
        # and find the relevant group, indexAdvisers form is :
        # 'delay_real_group_id__2014-04-16.9996934488', 'real_group_id_directeur-financier'
        # it is either a customAdviser row_id or a MeetingGroup id
        values = [term['v'] for term in collection.getRawQuery()
                  if term['i'] == 'indexAdvisers'][0]
        res = []
        for v in values:
            rowIdOrGroupId = v.replace('delay_real_group_id__', '').replace('real_group_id__', '')
            if hasattr(tool, rowIdOrGroupId):
                groupId = rowIdOrGroupId
                # append it only if not already into res and if
                # we have no 'row_id' for this adviser in adviceIndex
                if item and groupId not in res and \
                   (groupId in item.adviceIndex and not item.adviceIndex[groupId]['row_id']):
                    res.append(groupId)
                elif not item:
                    res.append(groupId)
            else:
                groupId = cfg._dataForCustomAdviserRowId(rowIdOrGroupId)['group']
                # append it only if not already into res and if
                # we have a 'row_id' for this adviser in adviceIndex
                if item and groupId not in res and \
                    (groupId in item.adviceIndex and
                     item.adviceIndex[groupId]['row_id'] == rowIdOrGroupId):
                    res.append(groupId)
                elif not item:
                    res.append(groupId)
        # remove duplicates
        return list(set(res))

    def _extraSearchesInfo(self, infos):
        """Add some specific searches."""
        cfg = self.getSelf()
        itemType = cfg.getItemTypeName()
        extra_infos = OrderedDict(
            [
                # Items in state 'proposed'
                ('searchproposeditems',
                 {
                     'subFolderId': 'searches_items',
                     'active': True,
                     'query':
                         [
                             {'i': 'portal_type',
                              'o': 'plone.app.querystring.operation.selection.is',
                              'v': [itemType, ]},
                             {'i': 'review_state',
                              'o': 'plone.app.querystring.operation.selection.is',
                              'v': ['proposed']}
                         ],
                     'sort_on': u'created',
                     'sort_reversed': True,
                     'showNumberOfItems': False,
                     'tal_condition': "python: not tool.userIsAmong(['reviewers'])",
                     'roles_bypassing_talcondition': ['Manager', ]
                 }
                 ),
                # Items in state 'validated'
                ('searchvalidateditems',
                 {
                     'subFolderId': 'searches_items',
                     'active': True,
                     'query':
                         [
                             {'i': 'portal_type',
                              'o': 'plone.app.querystring.operation.selection.is',
                              'v': [itemType, ]},
                             {'i': 'review_state',
                              'o': 'plone.app.querystring.operation.selection.is',
                              'v': ['validated']}
                         ],
                     'sort_on': u'created',
                     'sort_reversed': True,
                     'showNumberOfItems': False,
                     'tal_condition': "",
                     'roles_bypassing_talcondition': ['Manager', ]
                 }
                 ),
            ]
        )
        infos.update(extra_infos)
        return infos

    def extraAdviceTypes(self):
        '''See doc in interfaces.py.'''
        typesTool = api.portal.get_tool('portal_types')
        if 'meetingadvicefinances' in typesTool:
            return ['positive_finance', 'positive_with_remarks_finance',
                    'cautious_finance', 'negative_finance', 'not_given_finance',
                    'not_required_finance']
        return []


class MeetingNamurWorkflowActions(MeetingWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingCollegeWorkflowActions'''

    implements(IMeetingNamurWorkflowActions)
    security = ClassSecurityInfo()

    security.declarePrivate('doDecide')

    def doDecide(self, stateChange):
        '''We pass every item that is 'presented' in the 'itemfrozen'
           state.  It is the case for late items. Moreover, if
           MeetingConfig.initItemDecisionIfEmptyOnDecide is True, we
           initialize the decision field with content of Title+Description
           if decision field is empty.'''
        for item in self.context.getItems():
            # If deliberation (decision) is empty,
            # initialize it the decision field
            item._initDecisionFieldIfEmpty()

    security.declarePrivate('doBackToPublished')


    def doClose(self, stateChange):
        '''We initialize the decision field with content of Title+Description
           if no decision has already been written.'''
        MeetingWorkflowActions.doClose(self, stateChange)
        for item in self.context.getItems():
            # If the decision field is empty, initialize it
            item._initDecisionFieldIfEmpty()


    def doBackToPublished(self, stateChange):
        '''We do not impact items while going back from decided.'''
        pass

class MeetingNamurCollegeWorkflowActions(MeetingNamurWorkflowActions):
    '''inherit class'''
    implements(IMeetingNamurCollegeWorkflowActions)

class MeetingNamurCouncilWorkflowActions(MeetingNamurWorkflowActions):
    '''inherit class'''
    implements(IMeetingNamurCouncilWorkflowActions)

class MeetingNamurWorkflowConditions(MeetingWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingCollegeWorkflowConditions'''

    implements(IMeetingNamurWorkflowConditions)
    security = ClassSecurityInfo()

    security.declarePublic('mayDecide')

    def mayDecide(self):
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

class MeetingNamurCollegeWorkflowConditions(MeetingNamurWorkflowConditions):
    '''inherit class'''
    implements(IMeetingNamurCollegeWorkflowConditions)

class MeetingNamurCouncilWorkflowConditions(MeetingNamurWorkflowConditions):
    '''inherit class'''
    implements(IMeetingNamurCouncilWorkflowConditions)

class MeetingItemNamurWorkflowActions(MeetingItemWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCollegeWorkflowActions'''

    implements(IMeetingItemNamurWorkflowActions)
    security = ClassSecurityInfo()

    security.declarePrivate('doValidate')

    def doValidate(self, stateChange):
        # If it is a "late" item, we must potentially send a mail to warn MeetingManagers.
        item = self.context
        preferredMeeting = item.getPreferredMeeting()
        if preferredMeeting != 'whatever':
            # Get the meeting from its UID
            objs = item.uid_catalog.searchResults(UID=preferredMeeting)
            if objs:
                meeting = objs[0].getObject()
                if item.wfConditions().isLateFor(meeting):
                    sendMailIfRelevant(item, 'lateItem',
                                       'MeetingManager', isRole=True)
        # ask advice to the concerned alderman
        oa = item.getOptionalAdvisers()
        oal = list(oa)
        aldermans = item.adapted().getEchevinsForProposingGroup()
        for alderman in aldermans:
            if alderman not in oal:
                oal.append(alderman)
        oa = tuple(oal)
        item.setOptionalAdvisers(oa)
        # If the decision field is empty, initialize it
        item._initDecisionFieldIfEmpty()

    security.declarePrivate('doPresent')

    def doPresent(self, stateChange):
        MeetingItemWorkflowActions.doPresent(self, stateChange)
        item = self.context
        # If the decision field is empty, initialize it
        item._initDecisionFieldIfEmpty()

    security.declarePrivate('doAccept_but_modify')

    def doAccept_but_modify(self, stateChange):
        pass

    security.declarePrivate('doPre_accept')

    def doPre_accept(self, stateChange):
        pass

    security.declarePrivate('doCorrect')

    def doCorrect(self, stateChange):
        ''' If needed, suppress _budgetimpactreviewers role for this Item and
            clean decision field or copy description field in decision field.'''
        MeetingItemWorkflowActions.doCorrect(self, stateChange)
        item = self.context
        # send mail to creator if item return to owner
        if (item.queryState() == "itemcreated") or \
                (stateChange.old_state.id == "presented" and stateChange.new_state.id == "validated"):
            recipients = (item.portal_membership.getMemberById(str(item.Creator())).getProperty('email'),)
            sendMail(recipients, item, "itemMustBeCorrected")
            # Clear the decision field if item going back to service
            if item.queryState() == "itemcreated":
                item.setDecision("<p>&nbsp;</p>")
                item.reindexObject()
        if stateChange.old_state.id == "returned_to_proposing_group":
            # copy the description field into decision field
            item.setDecision("%s" % item.Description())
            item.reindexObject()
        # adapt MeetingBudgetImpactReviewerRole if needed
        item.adapted().giveMeetingBudgetImpactReviewerRole()

    security.declarePrivate('doReturn_to_proposing_group')

    def doReturn_to_proposing_group(self, stateChange):
        '''Cleaning decision field'''
        MeetingItemWorkflowActions.doReturn_to_proposing_group(self, stateChange)
        item = self.context
        item.setDecision("<p>&nbsp;</p>")
        item.reindexObject()

    security.declarePrivate('doItemFreeze')

    def doItemFreeze(self, stateChange):
        '''When an item is frozen, we must add local role MeetingBudgetReviewer '''
        item = self.context
        # adapt MeetingBudgetImpactReviewerRole if needed
        item.adapted().giveMeetingBudgetImpactReviewerRole()
        # If the decision field is empty, initialize it
        item._initDecisionFieldIfEmpty()

class MeetingItemNamurCollegeWorkflowActions(MeetingItemNamurWorkflowActions):
    '''inherit class'''
    implements(IMeetingItemNamurCollegeWorkflowActions)


class MeetingItemNamurCouncilWorkflowActions(MeetingItemNamurWorkflowActions):
    '''inherit class'''
    implements(IMeetingItemNamurCouncilWorkflowActions)


class MeetingItemNamurWorkflowConditions(MeetingItemWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCollegeWorkflowConditions'''

    implements(IMeetingItemNamurWorkflowConditions)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item  # Implements IMeetingItem

    security.declarePublic('mayDecide')

    def mayDecide(self):
        '''We may decide an item if the linked meeting is in relevant state.'''
        res = False
        meeting = self.context.getMeeting()
        if _checkPermission(ReviewPortalContent, self.context) and \
           meeting and meeting.adapted().isDecided():
            res = True
        return res


class MeetingItemNamurCollegeWorkflowConditions(MeetingItemNamurWorkflowConditions):
    '''inherit class'''
    implements(IMeetingItemNamurCollegeWorkflowConditions)


class MeetingItemNamurCouncilWorkflowConditions(MeetingItemNamurWorkflowConditions):
    '''inherit class'''
    implements(IMeetingItemNamurCouncilWorkflowConditions)


class CustomToolPloneMeeting(ToolPloneMeeting):
    '''Adapter that adapts a tool implementing ToolPloneMeeting to the
       interface IToolPloneMeetingCustom'''

    implements(IToolPloneMeetingCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item

    security.declarePublic('getSpecificAssemblyFor')

    def getSpecificAssemblyFor(self, assembly, startTxt=''):
        ''' Return the Assembly between two tag.
            This method is used in templates.
        '''
        # Pierre Dupont - Bourgmestre,
        # Charles Exemple - 1er Echevin,
        # Echevin Un, Echevin Deux excusé, Echevin Trois - Echevins,
        # Jacqueline Exemple, Responsable du CPAS
        # Absentes:
        # Mademoiselle x
        # ExcusÃ©s:
        # Monsieur Y, Madame Z
        res = []
        tmp = ['<p class="mltAssembly">']
        splitted_assembly = assembly.replace('<p>', '').replace('</p>', '').split('<br />')
        start_text = startTxt == ''
        for assembly_line in splitted_assembly:
            assembly_line = assembly_line.strip()
            # check if this line correspond to startTxt (in this cas, we can begin treatment)
            if not start_text:
                start_text = assembly_line.startswith(startTxt)
                if start_text:
                    # when starting treatment, add tag (not use if startTxt=='')
                    res.append(assembly_line)
                continue
            # check if we must stop treatment...
            if assembly_line.endswith(':'):
                break
            lines = assembly_line.split(',')
            cpt = 1
            my_line = ''
            for line in lines:
                if cpt == len(lines):
                    my_line = "%s%s<br />" % (my_line, line)
                    tmp.append(my_line)
                else:
                    my_line = "%s%s," % (my_line, line)
                cpt = cpt + 1
        if len(tmp) > 1:
            tmp[-1] = tmp[-1].replace('<br />', '')
            tmp.append('</p>')
        else:
            return ''
        res.append(''.join(tmp))
        return res


# ------------------------------------------------------------------------------

InitializeClass(CustomMeeting)
InitializeClass(CustomMeetingItem)
InitializeClass(CustomMeetingGroup)
InitializeClass(CustomMeetingConfig)
InitializeClass(MeetingNamurWorkflowActions)
InitializeClass(MeetingNamurWorkflowConditions)
InitializeClass(MeetingItemNamurWorkflowActions)
InitializeClass(MeetingItemNamurWorkflowConditions)
InitializeClass(CustomToolPloneMeeting)
# ------------------------------------------------------------------------------

class MLItemPrettyLinkAdapter(ItemPrettyLinkAdapter):
    """
      Override to take into account MeetingLiege use cases...
    """

    def _leadingIcons(self):
        """
          Manage icons to display before the icons managed by PrettyLink._icons.
        """
        # Default PM item icons
        icons = super(MLItemPrettyLinkAdapter, self)._leadingIcons()

        if self.context.isDefinedInTool():
            return icons

        # add an icon if item is confidential
        if self.context.getIsConfidentialItem():
            icons.append(('isConfidentialYes.png',
                          translate('isConfidentialYes',
                                    domain="PloneMeeting",
                                    context=self.request)))
        return icons

