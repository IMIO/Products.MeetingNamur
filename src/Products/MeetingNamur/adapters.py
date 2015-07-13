# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Copyright (c) 2007 by PloneGov
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
# ------------------------------------------------------------------------------
from appy.gen import No
from zope.interface import implements
from zope.i18n import translate
from AccessControl import ClassSecurityInfo
from Products.Archetypes.atapi import DisplayList
from Globals import InitializeClass
from Products.CMFCore.utils import getToolByName
from imio.helpers.xhtml import xhtmlContentIsEmpty
from Products.PloneMeeting.MeetingItem import MeetingItem, \
    MeetingItemWorkflowConditions, MeetingItemWorkflowActions
from Products.PloneMeeting.MeetingGroup import MeetingGroup
from Products.PloneMeeting.Meeting import MeetingWorkflowActions, \
    MeetingWorkflowConditions, Meeting
from Products.PloneMeeting.MeetingConfig import MeetingConfig
from Products.PloneMeeting.ToolPloneMeeting import ToolPloneMeeting
from Products.PloneMeeting.interfaces import IMeetingCustom, IMeetingItemCustom, \
    IMeetingGroupCustom, IMeetingConfigCustom, IToolPloneMeetingCustom
from Products.MeetingNamur.interfaces import \
    IMeetingItemNamurCollegeWorkflowConditions, IMeetingItemNamurCollegeWorkflowActions,\
    IMeetingNamurCollegeWorkflowConditions, IMeetingNamurCollegeWorkflowActions, \
    IMeetingItemNamurCouncilWorkflowConditions, IMeetingItemNamurCouncilWorkflowActions,\
    IMeetingNamurCouncilWorkflowConditions, IMeetingNamurCouncilWorkflowActions
from Products.PloneMeeting.utils import checkPermission, prepareSearchValue, sendMail, sendMailIfRelevant
from Products.CMFCore.permissions import ReviewPortalContent
from Products.PloneMeeting.model import adaptations
from Products.PloneMeeting.model.adaptations import WF_DOES_NOT_EXIST_WARNING, WF_APPLIED
from DateTime import DateTime
from Products.PloneMeeting.interfaces import IAnnexable

# Names of available workflow adaptations.
customWfAdaptations = ('return_to_proposing_group', )
MeetingConfig.wfAdaptations = customWfAdaptations
originalPerformWorkflowAdaptations = adaptations.performWorkflowAdaptations

RETURN_TO_PROPOSING_GROUP_CUSTOM_PERMISSIONS = {
    # view permissions
    'Access contents information':
    ('Manager', 'MeetingManager', 'MeetingMember', 'MeetingTaxController',
     'MeetingReviewer', 'MeetingObserverLocal', 'Reader', ),
    'View':
    ('Manager', 'MeetingManager', 'MeetingMember', 'MeetingTaxController',
     'MeetingReviewer', 'MeetingObserverLocal', 'Reader', ),
    'PloneMeeting: Read decision':
    ('Manager', 'MeetingManager', 'MeetingMember', 'MeetingTaxController',
     'MeetingReviewer', 'MeetingObserverLocal', 'Reader', ),
    'PloneMeeting: Read optional advisers':
    ('Manager', 'MeetingManager', 'MeetingMember', 'MeetingTaxController',
     'MeetingReviewer', 'MeetingObserverLocal', 'Reader', ),
    'PloneMeeting: Read decision annex':
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
    'PloneMeeting: Add MeetingFile':
    ('Manager', 'MeetingMember',  'MeetingManager',  'MeetingReviewer', ),
    'PloneMeeting: Write decision annex':
    ('Manager', 'MeetingMember',  'MeetingManager',  'MeetingReviewer', ),
    'PloneMeeting: Write optional advisers':
    ('Manager', 'MeetingMember',  'MeetingManager',  'MeetingReviewer', ),
    'PloneMeeting: Write optional advisers':
    ('Manager', 'MeetingMember',  'MeetingManager',  'MeetingReviewer', ),
    'PloneMeeting: Write budget infos':
    ('Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingBudgetImpactEditor', 'MeetingManager',
     'MeetingBudgetImpactReviewer', ),
    'MeetingNamur: Write description':
    ('Manager', 'MeetingMember', 'MeetingReviewer',),
    'MeetingNamur: Write certified signatures':
    ('Manager',),
    # MeetingManagers edit permissions
    'Delete objects':
    ['Manager', ],
    'PloneMeeting: Write item observations':
    ('Manager', 'MeetingManager', ),
}

adaptations.RETURN_TO_PROPOSING_GROUP_CUSTOM_PERMISSIONS = RETURN_TO_PROPOSING_GROUP_CUSTOM_PERMISSIONS


def customPerformWorkflowAdaptations(site, meetingConfig, logger, specificAdaptation=None):
    '''This function applies workflow changes as specified by the
       p_meetingConfig.'''

    wfAdaptations = specificAdaptation and [specificAdaptation, ] or meetingConfig.getWorkflowAdaptations()

    #while reinstalling a separate profile, the workflow could not exist
    wfTool = getToolByName(site, 'portal_workflow')
    meetingWorkflow = getattr(wfTool, meetingConfig.getMeetingWorkflow(), None)
    if not meetingWorkflow:
        logger.warning(WF_DOES_NOT_EXIST_WARNING % meetingConfig.getMeetingWorkflow())
        return
    itemWorkflow = getattr(wfTool, meetingConfig.getItemWorkflow(), None)
    if not itemWorkflow:
        logger.warning(WF_DOES_NOT_EXIST_WARNING % meetingConfig.getItemWorkflow())
        return

    error = meetingConfig.validate_workflowAdaptations(wfAdaptations)
    if error:
        raise Exception(error)

    for wfAdaptation in wfAdaptations:
        if not wfAdaptation in ['no_publication', ]:
            # call original perform of PloneMeeting
            originalPerformWorkflowAdaptations(site, meetingConfig, logger, specificAdaptation=wfAdaptation)
        elif wfAdaptation == 'no_publication':
            # we override the PloneMeeting's 'no_publication' wfAdaptation
            # First, update the meeting workflow
            wf = meetingWorkflow
            # Delete transitions 'publish' and 'backToPublished'
            for tr in ('publish', 'backToPublished'):
                if tr in wf.transitions:
                    wf.transitions.deleteTransitions([tr])
            # Update connections between states and transitions
            wf.states['frozen'].setProperties(
                title='frozen', description='',
                transitions=['backToCreated', 'decide'])
            wf.states['decided'].setProperties(
                title='decided', description='', transitions=['backToFrozen', 'close'])
            # Delete state 'published'
            if 'published' in wf.states:
                wf.states.deleteStates(['published'])
            # Then, update the item workflow.
            wf = itemWorkflow
            # Delete transitions 'itempublish' and 'backToItemPublished'
            for tr in ('itempublish', 'backToItemPublished'):
                if tr in wf.transitions:
                    wf.transitions.deleteTransitions([tr])
            # Update connections between states and transitions
            wf.states['itemfrozen'].setProperties(
                title='itemfrozen', description='',
                transitions=['accept', 'accept_but_modify', 'refuse', 'delay', 'pre_accept', 'backToPresented'])
            for decidedState in ['accepted', 'refused', 'delayed', 'accepted_but_modified']:
                wf.states[decidedState].setProperties(
                    title=decidedState, description='',
                    transitions=['backToItemFrozen', ])
            wf.states['pre_accepted'].setProperties(
                title='pre_accepted', description='',
                transitions=['accept', 'accept_but_modify', 'backToItemFrozen'])
            # Delete state 'published'
            if 'itempublished' in wf.states:
                wf.states.deleteStates(['itempublished'])
            logger.info(WF_APPLIED % ("no_publication", meetingConfig.getId()))
adaptations.performWorkflowAdaptations = customPerformWorkflowAdaptations


class CustomMeeting(Meeting):
    '''Adapter that adapts a meeting implementing IMeeting to the
       interface IMeetingCustom.'''

    implements(IMeetingCustom)
    security = ClassSecurityInfo()

    def __init__(self, meeting):
        self.context = meeting

    # Implements here methods that will be used by templates
    security.declarePublic('getPrintableItems')

    def getPrintableItems(self, itemUids, late=False, ignore_review_states=[],
                          privacy='*', oralQuestion='both', toDiscuss='both', categories=[],
                          excludedCategories=[], groupIds=[], firstNumber=1, renumber=False):
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
        # getItemsInOrder(uids), passing the correct uids and removing empty
        # uids.
        # privacy can be '*' or 'public' or 'secret'
        # oralQuestion can be 'both' or False or True
        # toDiscuss can be 'both' or 'False' or 'True'
        for elt in itemUids:
            if elt == '':
                itemUids.remove(elt)
        #no filtering, return the items ordered
        if not categories and not ignore_review_states and privacy == '*' and \
           oralQuestion == 'both' and toDiscuss == 'both':
            return self.context.getItemsInOrder(late=late, uids=itemUids)
        # Either, we will have to filter the state here and check privacy
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
            filteredItemUids.append(itemUid)
        #in case we do not have anything, we return an empty list
        if not filteredItemUids:
            return []
        else:
            items = self.context.getItemsInOrder(late=late, uids=filteredItemUids)
            if renumber:
                #return a list of tuple with first element the number and second
                #element the item itself
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
                        categoryList.insert(i+1, [meetingGroup, item])
                    else:
                        categoryList.insert(i+1, [meetingGroup])
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
                categoryList[groupIndex+1].append(item)

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

    def getPrintableItemsByCategory(self, itemUids=[], late=False,
                                    ignore_review_states=[], by_proposing_group=False, group_prefixes={},
                                    oralQuestion='both', toDiscuss='both',
                                    includeEmptyCategories=False, includeEmptyGroups=False,
                                    allNoConfidentialItems=False):
        '''Returns a list of (late-)items (depending on p_late) with
           category. Items being in a state whose name is in
           p_ignore_review_state will not be included in the result.
           If p_by_proposing_group is True, items are grouped by proposing group
           within every category. In this case, specifying p_group_prefixes will
           allow to consider all groups whose acronym starts with a prefix from
           this param prefix as a unique group. p_group_prefixes is a dict whose
           keys are prefixes and whose values are names of the logical big
           groups. A toDiscuss and oralQuestion can also be given, the item is a
           toDiscuss (oralQuestion) or not (or both) item.
           If p_includeEmptyCategories is True, categories for which no
           item is defined are included nevertheless. If p_includeEmptyGroups
           is True, proposing groups for which no item is defined are included
           nevertheless.'''
        # The result is a list of lists, where every inner list contains:
        # - at position 0: the category object (MeetingCategory or MeetingGroup)
        # - at position 1 to n: the items in this category
        # If by_proposing_group is True, the structure is more complex.
        # oralQuestion can be 'both' or False or True
        # toDiscuss can be 'both' or 'False' or 'True'
        # Every inner list contains:
        # - at position 0: the category object
        # - at positions 1 to n: inner lists that contain:
        #   * at position 0: the proposing group object
        #   * at positions 1 to n: the items belonging to this group.
        res = []
        items = []
        previousCatId = None
        tool = getToolByName(self.context, 'portal_plonemeeting')
        # Retrieve the list of items
        for elt in itemUids:
            if elt == '':
                itemUids.remove(elt)
        items = self.context.getItemsInOrder(late=late, uids=itemUids)
        if by_proposing_group:
            groups = tool.getMeetingGroups()
        else:
            groups = None
        if items:
            for item in items:
                # Check if the review_state has to be taken into account
                if item.queryState() in ignore_review_states:
                    continue
                elif not (oralQuestion == 'both' or item.getOralQuestion() == oralQuestion):
                    continue
                elif not (toDiscuss == 'both' or item.getToDiscuss() == toDiscuss):
                    continue
                elif allNoConfidentialItems:
                    user = self.context.portal_membership.getAuthenticatedMember()
                    userCanView = user.has_permission('View', item)
                    if item.getIsConfidentialItem() and not userCanView:
                        continue
                currentCat = item.getCategory(theObject=True)
                currentCatId = currentCat.getId()
                if currentCatId != previousCatId:
                    # Add the item to a new category, excepted if the
                    # category already exists.
                    catExists = False
                    for catList in res:
                        if catList[0] == currentCat:
                            catExists = True
                            break
                    if catExists:
                        self._insertItemInCategory(catList, item, by_proposing_group, group_prefixes, groups)
                    else:
                        res.append([currentCat])
                        self._insertItemInCategory(res[-1], item, by_proposing_group, group_prefixes, groups)
                    previousCatId = currentCatId
                else:
                    # Append the item to the same category
                    self._insertItemInCategory(res[-1], item, by_proposing_group, group_prefixes, groups)
        if includeEmptyCategories:
            meetingConfig = tool.getMeetingConfig(self.context)
            allCategories = meetingConfig.getCategories()
            usedCategories = [elem[0] for elem in res]
            for cat in allCategories:
                if cat not in usedCategories:
                    #no empty service, we want only show department
                    if cat.getAcronym().find('-') > 0:
                        continue
                    else:
                        #no empty department
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
        return res

    security.declarePublic('getPrintableItemsByNumCategory')

    def getPrintableItemsByNumCategory(self, late=False, uids=[],
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

        itemsGetter = self.context.getItems
        if late:
            itemsGetter = self.context.getLateItems
        items = itemsGetter()
        if allItems:
            items = self.context.getItems() + self.context.getLateItems()
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
                    #first value of the list is the category object
                    res[catNum][0] = item.getCategory(True)
                    #second value of the list is a list of items
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
                    k = k+1
                    ressorti1.append([res[i][1][j], k])
                ressorti.append(ressorti1)
                ressort.append(ressorti)
        return ressort


class CustomMeetingItem(MeetingItem):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCustom.'''
    implements(IMeetingItemCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item

    security.declarePublic('itemPositiveDecidedStates')

    def itemPositiveDecidedStates(self):
        '''See doc in interfaces.py.'''
        return ('accepted', 'accepted_but_modified', )

    security.declarePublic('getEchevinsForProposingGroup')

    def getEchevinsForProposingGroup(self):
        '''Returns all echevins defined for the proposing group'''
        res = []
        tool = getToolByName(self.context, "portal_plonemeeting")
        for group in tool.getMeetingGroups():
            if self.context.getProposingGroup() in group.getEchevinServices():
                res.append(group.id)
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

    security.declarePublic('getIcons')

    def getIcons(self, inMeeting, meeting):
        '''Check docstring in PloneMeeting interfaces.py.'''
        item = self.getSelf()
        # Default PM item icons
        res = MeetingItem.getIcons(item, inMeeting, meeting)
        # Add our icons for accepted_but_modified and pre_accepted
        itemState = item.queryState()
        if itemState == 'accepted_but_modified':
            res.append(('accepted_but_modified.png', 'icon_help_accepted_but_modified'))
        elif itemState == 'pre_accepted':
            res.append(('pre_accepted.png', 'icon_help_pre_accepted'))
        if item.getIsConfidentialItem():
            res.append(('isConfidentialYes.png', 'isConfidentialYes'))
        return res

    def _initCustomDecisionFieldIfEmpty(self):
        '''
          If decision field is empty, it will be initialized
          with data coming from title and description.
        '''
        # set keepWithNext to False as it will add a 'class' and so
        # xhtmlContentIsEmpty will never consider it empty...
        item = self.getSelf()
        if xhtmlContentIsEmpty(item.getDeliberation(keepWithNext=False)):
            item.setDecision("%s" % item.Description())
            item.reindexObject()

    security.declarePublic('getAllAnnexes')

    def printAllAnnexes(self):
        ''' Printing Method use in templates :
            return all viewable annexes for item '''
        res = []
        annexesByType = IAnnexable(self.context).getAnnexesByType('item')
        for annexes in annexesByType:
            for annex in annexes:
                title = annex['Title'].replace('&', '&amp;')
                url = getattr(self.context, annex['id']).absolute_url()
                res.append('<a href="%s">%s</a><br/>' % (url, title))
        return ('\n'.join(res))

    security.declarePublic('getFormatedAdvice ')

    def printFormatedAdvice(self):
        ''' Printing Method use in templates :
            return formated advice'''
        res = []
        item = self.getSelf()
        keys = item.getAdvicesByType().keys()
        for key in keys:
            for advice in item.getAdvicesByType()[key]:
                if advice['type'] == 'not_given':
                    continue
                comment = ''
                if advice['comment']:
                    comment = advice['comment']
                res.append({'type': item.i18n(key).encode('utf-8'), 'name': advice['name'].encode('utf-8'),
                            'comment': comment})
        return res

    security.declarePublic('customshowDuplicateItemAction')

    def customshowDuplicateItemAction(self):
        '''Condition for displaying the 'duplicate' action in the interface.
           Returns True if the user can duplicate the item.'''
        # Conditions for being able to see the "duplicate an item" action:
        # - the user is not Plone-disk-aware;
        # - the user is creator in some group;
        # - the user must be able to see the item if it is private.
        # The user will duplicate the item in his own folder.
        tool = getToolByName(self, 'portal_plonemeeting')
        item = self.getSelf()
        ignoreDuplicateButton = item.queryState() == 'pre_accepted'
        if self.isDefinedInTool() or not tool.userIsAmong('creators') \
           or not self.isPrivacyViewable() or ignoreDuplicateButton:
            return False
        return True
    MeetingItem.showDuplicateItemAction = customshowDuplicateItemAction

    def onDuplicated(self, orig):
        '''After item's cloning, we copy in description field the decision field
           and clear decision field.
        '''
        item = self.getSelf()
        #copy decision from source items in destination's deliberation if item is accepted
        if item.queryState() in ['accepted', 'accepted_but_modified']:
            item.setDescription(orig.getDecision())
        #clear decision for new item
        item.setDecision('')

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
        return item.i18n(state, domain='plone')

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
        res = ['grpBudgetInfos', 'itemCertifiedSignatures', 'isConfidentialItem']
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
        tool = getToolByName(self, "portal_plonemeeting")
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

    security.declarePublic('listCdldProposingGroup')

    def listCdldProposingGroup(self):
        '''Returns a list of groups that can be selected for cdld synthesis field
        '''
        tool = getToolByName(self, 'portal_plonemeeting')
        res = []
        # add delay-aware optionalAdvisers
        customAdvisers = self.getSelf().getCustomAdvisers()
        for customAdviser in customAdvisers:
            groupId = customAdviser['group']
            groupDelay = customAdviser['delay']
            groupDelayLabel = customAdviser['delay_label']
            group = getattr(tool, groupId, None)
            groupKey = '%s__%s__(%s)' % (groupId, groupDelay, groupDelayLabel)
            groupValue = '%s - %s (%s)' % (group.Title(), groupDelay, groupDelayLabel)
            if group:
                res.append((groupKey, groupValue))
        # only let select groups for which there is at least one user in
        nonEmptyMeetingGroups = tool.getMeetingGroups(notEmptySuffix='advisers')
        if nonEmptyMeetingGroups:
            for mGroup in nonEmptyMeetingGroups:
                res.append(('%s____' % mGroup.getId(), mGroup.getName()))
        res = DisplayList(res)
        return res
    MeetingConfig.listCdldProposingGroup = listCdldProposingGroup

    security.declarePublic('searchCDLDItems')

    def searchCDLDItems(self, sortKey='', sortOrder='', filterKey='', filterValue='', **kwargs):
        '''Queries all items for cdld synthesis'''
        groups = []
        cdldProposingGroups = self.getSelf().getCdldProposingGroup()
        for cdldProposingGroup in cdldProposingGroups:
            groupId = cdldProposingGroup.split('__')[0]
            delay = ''
            if cdldProposingGroup.split('__')[1]:
                delay = 'delay__'
            groups.append('%s%s' % (delay, groupId))
        # advised items are items that has an advice in a particular review_state
        # just append every available meetingadvice state: we want "given" advices.
        # this search will only return 'delay-aware' advices
        wfTool = getToolByName(self, 'portal_workflow')
        adviceWF = wfTool.getWorkflowsFor('meetingadvice')[0]
        adviceStates = adviceWF.states.keys()
        groupIds = []
        advice_index__suffixs = ('advice_delay_exceeded', 'advice_not_given', 'advice_not_giveable')
        # advice given
        for adviceState in adviceStates:
            groupIds += [g + '_%s' % adviceState for g in groups]
        #advice not given
        for advice_index__suffix in advice_index__suffixs:
            groupIds += [g + '_%s' % advice_index__suffix for g in groups]
        # Create query parameters
        fromDate = DateTime(2013, 01, 01)
        toDate = DateTime(2014, 12, 31, 23, 59)
        params = {'portal_type': self.getItemTypeName(),
                  # KeywordIndex 'indexAdvisers' use 'OR' by default
                  'indexAdvisers': groupIds,
                  'created': {'query': [fromDate, toDate], 'range': 'minmax'},
                  'sort_on': sortKey,
                  'sort_order': sortOrder, }
        # Manage filter
        if filterKey:
            params[filterKey] = prepareSearchValue(filterValue)
        # update params with kwargs
        params.update(kwargs)
        # Perform the query in portal_catalog
        brains = self.portal_catalog(**params)
        res = []
        fromDate = DateTime(2014, 01, 01)  # redefine date to get advice in 2014
        for brain in brains:
            obj = brain.getObject()
            if obj.getMeeting() and obj.getMeeting().getDate() >= fromDate and obj.getMeeting().getDate() <= toDate:
                res.append(brain)
        return res
    MeetingConfig.searchCDLDItems = searchCDLDItems

    security.declarePublic('printCDLDItems')

    def printCDLDItems(self):
        '''
        Returns a list of advice for synthesis document (CDLD)
        '''
        meetingConfig = self.getSelf()
        brains = meetingConfig.context.searchCDLDItems()
        res = []
        groups = []
        cdldProposingGroups = meetingConfig.getCdldProposingGroup()
        for cdldProposingGroup in cdldProposingGroups:
            groupId = cdldProposingGroup.split('__')[0]
            delay = False
            if cdldProposingGroup.split('__')[1]:
                delay = True
            if not (groupId, delay) in groups:
                groups.append((groupId, delay))
        for brain in brains:
            item = brain.getObject()
            advicesIndex = item.adviceIndex
            for groupId, delay in groups:
                if groupId in advicesIndex:
                    advice = advicesIndex[groupId]
                    if advice['delay'] and not delay:
                        continue
                    if not (advice, item) in res:
                        res.append((advice, item))
        return res


class CustomMeetingConfig(MeetingConfig):
    '''Adapter that adapts a meetingConfig implementing IMeetingConfig to the
       interface IMeetingConfigCustom.'''

    implements(IMeetingConfigCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item


class MeetingNamurCollegeWorkflowActions(MeetingWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingNamurCollegeWorkflowActions'''

    implements(IMeetingNamurCollegeWorkflowActions)
    security = ClassSecurityInfo()

    security.declarePrivate('doDecide')

    def doDecide(self, stateChange):
        '''We pass every item that is 'presented' in the 'itemfrozen'
           state.  It is the case for late items. We initialize the decision
           field with content of Title+Description if no decision has already
           been written.'''
        for item in self.context.getAllItems(ordered=True):
            # If the decision field is empty, initialize it
            item.adapted()._initCustomDecisionFieldIfEmpty()


class MeetingNamurCollegeWorkflowConditions(MeetingWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingNamurCollegeWorkflowConditions'''

    implements(IMeetingNamurCollegeWorkflowConditions)
    security = ClassSecurityInfo()

    security.declarePublic('mayFreeze')

    def mayFreeze(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            res = True  # At least at present
            if not self.context.getRawItems():
                res = No(translate('item_required_to_publish', domain='PloneMeeting', context=self.context.REQUEST))
        return res

    security.declarePublic('mayClose')

    def mayClose(self):
        res = False
        # The user just needs the "Review portal content" permission on the
        # object to close it.
        if checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayDecide')

    def mayDecide(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            res = True
        return res


class MeetingItemNamurCollegeWorkflowActions(MeetingItemWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemNamurCollegeWorkflowActions'''

    implements(IMeetingItemNamurCollegeWorkflowActions)
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
        item.adapted()._initCustomDecisionFieldIfEmpty()

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
        #send mail to creator if item return to owner
        if (item.queryState() == "itemcreated") or \
           (stateChange.old_state.id == "presented" and stateChange.new_state.id == "validated"):
            recipients = (item.portal_membership.getMemberById(str(item.Creator())).getProperty('email'),)
            sendMail(recipients, item, "itemMustBeCorrected")
            # Clear the decision field if item going back to creator
            item.setDecision("")
            item.reindexObject()
        if stateChange.old_state.id == "returned_to_proposing_group":
            # copy the description field into decision field
            item.setDecision("%s" % item.Description())
            item.reindexObject()
        #adapt MeetingBudgetImpactReviewerRole if needed
        item.adapted().giveMeetingBudgetImpactReviewerRole()

    security.declarePrivate('doReturn_to_proposing_group')

    def doReturn_to_proposing_group(self, stateChange):
        '''Cleaning decision field'''
        MeetingItemWorkflowActions.doReturn_to_proposing_group(self, stateChange)
        item = self.context
        item.setDecision("")
        item.reindexObject()

    security.declarePrivate('doItemFreeze')

    def doItemFreeze(self, stateChange):
        '''When an item is frozen, we must add local role MeetingBudgetReviewer '''
        item = self.context
        item.adapted().giveMeetingBudgetImpactReviewerRole()


class MeetingItemNamurCollegeWorkflowConditions(MeetingItemWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemNamurCollegeWorkflowConditions'''

    implements(IMeetingItemNamurCollegeWorkflowConditions)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item  # Implements IMeetingItem

    security.declarePublic('mayDecide')

    def mayDecide(self):
        '''We may decide an item if the linked meeting is in relevant state.'''
        res = False
        meeting = self.context.getMeeting()
        if checkPermission(ReviewPortalContent, self.context) and \
           meeting and meeting.adapted().isDecided():
            res = True
        return res


class MeetingNamurCouncilWorkflowActions(MeetingNamurCollegeWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingNamurCouncilWorkflowActions'''

    implements(IMeetingNamurCouncilWorkflowActions)
    security = ClassSecurityInfo()

    security.declarePrivate('doDecide')

    def doDecide(self, stateChange):
        '''We pass every item that is 'presented' in the 'itemfrozen'
           state.  It is the case for late items. We initialize the decision
           field with content of Title+Description if no decision has already
           been written.'''
        for item in self.context.getAllItems(ordered=True):
            # If the decision field is empty, initialize it
            item.adapted()._initCustomDecisionFieldIfEmpty()

    security.declarePrivate('doBackToPublished')

    def doBackToPublished(self, stateChange):
        '''We do not impact items while going back from decided.'''
        pass


class MeetingNamurCouncilWorkflowConditions(MeetingNamurCollegeWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingNamurCouncilWorkflowConditions'''

    implements(IMeetingNamurCouncilWorkflowConditions)
    security = ClassSecurityInfo()

    security.declarePublic('mayClose')

    def mayClose(self):
        res = False
        # The user just needs the "Review portal content" permission on the
        # object to close it.
        if checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayDecide')

    def mayDecide(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            res = True
        return res


class MeetingItemNamurCouncilWorkflowActions(MeetingItemNamurCollegeWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemNamurCouncilWorkflowActions'''

    implements(IMeetingItemNamurCouncilWorkflowActions)
    security = ClassSecurityInfo()


class MeetingItemNamurCouncilWorkflowConditions(MeetingItemNamurCollegeWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemNamurCouncilWorkflowConditions'''

    implements(IMeetingItemNamurCouncilWorkflowConditions)
    security = ClassSecurityInfo()

    security.declarePublic('mayFreeze')

    def mayFreeze(self):
        """
          A MeetingManager may freeze an item if the meeting is at least frozen
        """
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            if self.context.hasMeeting() and \
               (self.context.getMeeting().queryState() in ('frozen',
                                                           'published',
                                                           'decided',
                                                           'closed',
                                                           'decisions_published', )):
                res = True
        return res

    security.declarePublic('mayPublish')

    def mayPublish(self):
        """
          A MeetingManager may publish (itempublish) an item if the meeting is at least published
        """
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            if self.context.hasMeeting() and \
               (self.context.getMeeting().queryState() in ('published', 'decided', 'closed', 'decisions_published',)):
                res = True
        return res

    security.declarePublic('mayDecide')

    def mayDecide(self):
        '''We may decide an item if the linked meeting is in relevant state.'''
        res = False
        meeting = self.context.getMeeting()
        if checkPermission(ReviewPortalContent, self.context) and \
           meeting and meeting.adapted().isDecided():
            res = True
        return res


class CustomToolPloneMeeting(ToolPloneMeeting):
    '''Adapter that adapts a tool implementing ToolPloneMeeting to the
       interface IToolPloneMeetingCustom'''

    implements(IToolPloneMeetingCustom)
    security = ClassSecurityInfo()

    security.declarePublic('getSpecificAssemblyFor')

    def getSpecificAssemblyFor(self, assembly, startTxt=''):
        ''' Return the Assembly between two tag.
            This method is use in template
        '''
        #Pierre Dupont - Bourgmestre,
        #Charles Exemple - 1er Echevin,
        #Echevin Un, Echevin Deux excusé, Echevin Trois - Echevins,
        #Jacqueline Exemple, Responsable du CPAS
        #Absentes:
        #Mademoiselle x
        #Excusés:
        #Monsieur Y, Madame Z
        res = []
        tmp = ['<p class="mltAssembly">']
        splitted_assembly = assembly.replace('<p>', '').replace('</p>', '').split('<br />')
        start_text = startTxt == ''
        for assembly_line in splitted_assembly:
            assembly_line = assembly_line.strip()
            #check if this line correspond to startTxt (in this cas, we can begin treatment)
            if not start_text:
                start_text = assembly_line.startswith(startTxt)
                if start_text:
                    #when starting treatment, add tag (not use if startTxt=='')
                    res.append(assembly_line)
                continue
            #check if we must stop treatment...
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
InitializeClass(MeetingNamurCollegeWorkflowActions)
InitializeClass(MeetingNamurCollegeWorkflowConditions)
InitializeClass(MeetingItemNamurCollegeWorkflowActions)
InitializeClass(MeetingItemNamurCollegeWorkflowConditions)
InitializeClass(MeetingItemNamurCouncilWorkflowActions)
InitializeClass(MeetingItemNamurCouncilWorkflowConditions)
InitializeClass(MeetingNamurCouncilWorkflowActions)
InitializeClass(MeetingNamurCouncilWorkflowConditions)
InitializeClass(CustomToolPloneMeeting)
# ------------------------------------------------------------------------------
