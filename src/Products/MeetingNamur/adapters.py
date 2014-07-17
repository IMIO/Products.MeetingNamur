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
from appy.gen.utils import Keywords
from zope.interface import implements
from zope.i18n import translate
from AccessControl import ClassSecurityInfo
from Products.Archetypes.atapi import DisplayList
from Globals import InitializeClass
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
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
from Products.PloneMeeting.utils import checkPermission, sendMail, sendMailIfRelevant
from Products.CMFCore.permissions import ReviewPortalContent, ModifyPortalContent
from Products.PloneMeeting.utils import getCurrentMeetingObject
from Products.PloneMeeting import PloneMeetingError
from Products.PloneMeeting.model import adaptations
from Products.PloneMeeting.model.adaptations import *
from Products.PloneMeeting.config import DEFAULT_COPIED_FIELDS
import logging
logger = logging.getLogger('PloneMeeting')

# Names of available workflow adaptations.
customWfAdaptations = ('no_global_observation', 'creator_initiated_decisions',
                       'only_creator_may_delete', 'pre_validation',
                       'no_proposal', 'everyone_reads_all',
                       'creator_edits_unless_closed', 'local_meeting_managers', 'return_to_proposing_group',)
MeetingConfig.wfAdaptations = customWfAdaptations
originalPerformWorkflowAdaptations = adaptations.performWorkflowAdaptations


def customPerformWorkflowAdaptations(site, meetingConfig, logger, specificAdaptation=None):
    '''This function applies workflow changes as specified by the
       p_meetingConfig.'''

    wfAdaptations = specificAdaptation and [specificAdaptation, ] or meetingConfig.getWorkflowAdaptations()

    #while reinstalling a separate profile, the workflow could not exist
    meetingWorkflow = getattr(site.portal_workflow, meetingConfig.getMeetingWorkflow(), None)
    if not meetingWorkflow:
        logger.warning(WF_DOES_NOT_EXIST_WARNING % meetingConfig.getMeetingWorkflow())
        return
    itemWorkflow = getattr(site.portal_workflow, meetingConfig.getItemWorkflow(), None)
    if not itemWorkflow:
        logger.warning(WF_DOES_NOT_EXIST_WARNING % meetingConfig.getItemWorkflow())
        return

    error = meetingConfig.validate_workflowAdaptations(wfAdaptations)
    if error:
        raise Exception(error)

    for wfAdaptation in wfAdaptations:
        if not wfAdaptation in ['no_publication', 'add_published_state', ]:
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
        elif wfAdaptation == 'add_published_state':
            # "add_published_state" add state 'decisions_published' in the meeting workflow
            # The idea is to let people "finalize" the meeting even after is has been
            # decisions_published, a finalized version, ie, some hours or minutes before the meeting begins.
            # When the meeting is in decided state, we hide the decision for no-meetingManager
            # First, update the meeting workflow
            wf = meetingWorkflow
            # add state 'decision_published'
            if 'decisions_published' not in wf.states:
                wf.states.addState('decisions_published')
            # Create new transitions linking the new state to existing ones
            # ('decided' and 'closed').
            # add transitions 'publish_decision' and 'backToDecisionPublished'
            for tr in ('publish_decisions', 'backToDecisionsPublished'):
                if tr not in wf.transitions:
                    wf.transitions.addTransition(tr)
            transition = wf.transitions['publish_decisions']
            transition.setProperties(title='publish_decisions',
                                     new_state_id='decisions_published', trigger_type=1, script_name='',
                                     actbox_name='publish_decisions', actbox_url='', actbox_category='workflow',
                                     props={'guard_expr': 'python:here.wfConditions().mayPublishDecisions()'})
            transition = wf.transitions['backToDecisionsPublished']
            transition.setProperties(title='backToDecisionsPublished',
                                     new_state_id='decisions_published', trigger_type=1, script_name='',
                                     actbox_name='backToDecisionsPublished', actbox_url='',
                                     actbox_category='workflow',
                                     props={'guard_expr': 'python:here.wfConditions().mayCorrect()'})
            # Update connections between states and transitions
            wf.states['decided'].setProperties(
                title='decided', description='',
                transitions=['backToFrozen', 'publish_decisions'])
            wf.states['decisions_published'].setProperties(
                title='decisions_published', description='',
                transitions=['backToDecided', 'close'])
            wf.states['closed'].setProperties(
                title='closed', description='',
                transitions=['backToDecisionsPublished', ])
            # Initialize permission->roles mapping for new state "decisions_published",
            # which is the same as state "frozen" (or "decided")in the previous setting.
            frozen = wf.states['frozen']
            decisions_published = wf.states['decisions_published']
            for permission, roles in frozen.permission_roles.iteritems():
                decisions_published.setPermission(permission, 0, roles)
            # Transition "backToPublished" must be protected by a popup, like
            # any other "correct"-like transition.
            toConfirm = meetingConfig.getTransitionsToConfirm()
            if 'Meeting.backToDecisionsPublished' not in toConfirm:
                toConfirm = list(toConfirm)
                toConfirm.append('Meeting.backToDecisionsPublished')
                meetingConfig.setTransitionsToConfirm(toConfirm)
            # State "decisions_published" must be selected in DecisionTopicStates (queries)
            queryStates = meetingConfig.getDecisionTopicStates()
            if 'decisions_published' not in queryStates:
                queryStates = list(queryStates)
                queryStates.append('decisions_published')
                meetingConfig.setDecisionTopicStates(queryStates)
                # Update the topics definitions for taking this into account.
                meetingConfig.updateTopics()
            logger.info(WF_APPLIED % ("add_published_state", meetingConfig.getId()))
adaptations.performWorkflowAdaptations = customPerformWorkflowAdaptations


originalValidate_workflowAdaptations = MeetingConfig.validate_workflowAdaptations


def validate_workflowAdaptations(self, v):
    '''This method ensures that the combination of used workflow
       adaptations is valid.'''
    pmmsg = originalValidate_workflowAdaptations(self, v)
    if pmmsg:
        return pmmsg

    msg = translate('wa_conflicts', domain='PloneMeeting', context=self.REQUEST)
    # 'add_published_state' and 'no_publication' are not working together
    if ('add_published_state' in v) and ('no_publication' in v):
        return msg
MeetingConfig.validate_workflowAdaptations = validate_workflowAdaptations


class CustomMeeting(Meeting):
    '''Adapter that adapts a meeting implementing IMeeting to the
       interface IMeetingCustom.'''

    implements(IMeetingCustom)
    security = ClassSecurityInfo()

    def __init__(self, meeting):
        self.context = meeting

    security.declarePublic('isDecided')
    def isDecided(self):
        meeting = self.getSelf()
        return meeting.queryState() in ('decided', 'closed', 'archived', 'decisions_published', )

    # Implements here methods that will be used by templates
    security.declarePublic('getPrintableItems')
    def getPrintableItems(self, itemUids, late=False, ignore_review_states=[],
                          privacy='*', oralQuestion='both', toDiscuss='both', categories=[],
                          excludedCategories=[], firstNumber=1, renumber=False):
        '''Returns a list of items.
           An extra list of review states to ignore can be defined.
           A privacy can also be given, and the fact that the item is an
           oralQuestion or not (or both). Idem with toDiscuss.
           Some specific categories can be given or some categories to exchude.
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
                                    includeEmptyCategories=False, includeEmptyGroups=False):
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
        # Retrieve the list of items
        for elt in itemUids:
            if elt == '':
                itemUids.remove(elt)
        items = self.context.getItemsInOrder(late=late, uids=itemUids)
        if by_proposing_group:
            groups = self.context.portal_plonemeeting.getMeetingGroups(onlyActive=True)
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
            meetingConfig = self.context.portal_plonemeeting.getMeetingConfig(
                self.context)
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

    security.declarePublic('getPreviousMeeting')
    def getPreviousMeeting(self, searchMeetingsInterval=60):
        '''Gets the previous meeting based on meeting date. We only search among
           meetings in the previous p_searchMeetingsInterval, which is a number
           of days. If no meeting is found, the method returns None.'''
        meetingDate = self.context.getDate()
        meetingConfig = self.context.portal_plonemeeting.getMeetingConfig(
            self.context)
        meetingTypeName = meetingConfig.getMeetingTypeName()
        allMeetings = self.context.portal_catalog(
            portal_type=meetingTypeName,
            getDate={'query': self.context.getDate()-searchMeetingsInterval,
                     'range': 'min'},
            sort_on='getDate', sort_order='reverse')
        res = None
        for meeting in allMeetings:
            if (meeting.getObject().getDate() < meetingDate):
                res = meeting
                break
        if res:
            res = res.getObject()
        return res

    security.declarePublic('showItemAdvices')
    def showItemAdvices(self):
        '''See doc in interfaces.py.'''
        return True

    security.declarePublic('showAllItemsAtOnce')
    def showAllItemsAtOnce(self):
        '''Must I show the Kupu field that allows to edit all "normal" and
           "late" items at once ?'''
        # I must have 'write' permissions on every item in order to do this.
        # and the meeting must not be decided
        # deactivate this field as it does not work anymore...
        return False
        if self.getItems():
            if self.adapted().isDecided():
                return False
            else:
                writePerms = (ModifyPortalContent,)
            currentUser = self.portal_membership.getAuthenticatedMember()
            for item in self.getAllItems():
                for perm in writePerms:
                    if not currentUser.has_permission(perm, item):
                        return False
            return True
        else:
            return False
    Meeting.showAllItemsAtOnce = showAllItemsAtOnce


class CustomMeetingItem(MeetingItem):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCustom.'''
    implements(IMeetingItemCustom)
    security = ClassSecurityInfo()

    customItemPositiveDecidedStates = ('accepted', 'accepted_but_modified', )
    MeetingItem.itemPositiveDecidedStates = customItemPositiveDecidedStates

    def __init__(self, item):
        self.context = item

    security.declarePublic('getMeetingsAcceptingItems')
    def getMeetingsAcceptingItems(self):
        '''Overrides the default method so we only display meetings that are
           in the 'created' or 'frozen' state.'''
        pmtool = getToolByName(self.context, "portal_plonemeeting")
        catalogtool = getToolByName(self.context, "portal_catalog")
        meetingPortalType = pmtool.getMeetingConfig(self.context).getMeetingTypeName()
        # If the current user is a meetingManager (or a Manager),
        # he is able to add a meetingitem to a 'decided' meeting.
        review_state = ['created', 'frozen', ]
        if self.context.portal_plonemeeting.isManager():
            review_state += ['decided', 'published', ]
        res = catalogtool.unrestrictedSearchResults(
            portal_type=meetingPortalType,
            review_state=review_state,
            sort_on='getDate')
        # Frozen meetings may still accept "late" items.
        return res

    security.declarePublic('mayBeLinkedToTasks')
    def mayBeLinkedToTasks(self):
        '''See doc in interfaces.py.'''
        item = self.getSelf()
        res = False
        if (item.queryState() in ('accepted', 'refused', 'delayed')):
            res = True
        return res

    security.declarePublic('getCertifiedSignatures')
    def getCertifiedSignatures(self, forceUseCertifiedSignaturesField=False):
        '''Gets the certified signatures for this item.
           Either use signatures defined on the proposing MeetingGroup if exists,
           or use the meetingConfig certified signatures.'''
        item = self.getSelf()
        if not item.hasMeeting():
            return '', False
        signature = item.getProposingGroup(theObject=True).getSignatures()
        hasGroupSignature = True
        if not signature:
            meetingConfig = item.portal_plonemeeting.getMeetingConfig(item)
            # either use the certifiedSignatures or check for certified signatories
            # from MeetingUsers having the usage 'voter' and being 'default signatories'
            # first check if we use MeetingUsers
            if not meetingConfig.isUsingMeetingUsers() or forceUseCertifiedSignaturesField:
                signature = meetingConfig.getCertifiedSignatures()
                hasGroupSignature = False
            else:
                # we use MeetingUsers
                signatories = meetingConfig.getMeetingUsers(usages=('signer',))
                res = []
                for signatory in signatories:
                    if signatory.getSignatureIsDefault():
                        particule = signatory.getGender() == 'm' and 'Le' or 'La'
                        res.append("%s %s" % (particule, signatory.getDuty()))
                        res.append("%s" % signatory.Title())
                signature = '\n'.join(res)
        return signature, hasGroupSignature

    def getEchevinsForProposingGroup(self):
        '''Returns all echevins defined for the proposing group'''
        res = []
        pmtool = getToolByName(self.context, "portal_plonemeeting")
        for group in pmtool.getMeetingGroups(onlyActive=True):
            if self.context.getProposingGroup() in group.getEchevinServices():
                res.append(group.id)
        return res

    def listGrpBudgetInfosAdviser(self):
        '''Returns a list of groups that can be selected on an item to modify budgetInfos field.
        acronym group start with DGF'''
        res = []
        res.append(('', self.utranslate('make_a_choice', domain='PloneMeeting')))
        pmtool = getToolByName(self, "portal_plonemeeting")
        for group in pmtool.getMeetingGroups(onlyActive=True):
            if group.acronym.startswith('DGF'):
                res.append((group.id, group.getProperty('title')))
        return DisplayList(tuple(res))
    MeetingItem.listGrpBudgetInfosAdviser = listGrpBudgetInfosAdviser

    def giveMeetingBudgetImpactReviewerRole(self):
        '''Add MeetingBudgetImpactReviewer role when on an item, a group is choosen in BudgetInfosAdviser and state is,
           at least, "itemFrozen". Remove role for other grp_budgetimpactreviewers or remove all
           grp_budgetimpactreviewers in local role if state back in state before itemFrozen.
        '''
        item = self.getSelf()
        grp_roles = []
        if item.queryState() in ('itemfrozen', 'accepted', 'delayed', 'accepted_but_modified',
                                 'pre_accepted', 'refused'):
            #add new MeetingBudgetImpactReviewerRole
            for grpBudgetInfo in item.grpBudgetInfos:
                grp_role = '%s_budgetimpactreviewers' % grpBudgetInfo
                #for each group_budgetimpactreviewers add new local roles
                if grpBudgetInfo:
                    grp_roles.append(grp_role)
                    item.manage_addLocalRoles(grp_role, ('MeetingObserverLocal', 'MeetingBudgetImpactReviewer',))
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
        return res

    security.declarePublic('printAdvicesInfos')
    def printAdvicesInfos(self):
        '''Helper method to have a printable version of advices.'''
        item = self.getSelf()
        itemAdvicesByType = item.getAdvicesByType()
        res = "<p><u>%s :</u></p>" % translate('PloneMeeting_label_advices',
                                               domain='PloneMeeting',
                                               context=item.REQUEST)
        if itemAdvicesByType:
            res = res + "<p>"
        for adviceType in itemAdvicesByType:
            for advice in itemAdvicesByType[adviceType]:
                res = res + u"<u>%s :</u> %s<br />" % (advice['name'], translate([advice['type']][0],
                                                                                 domain='PloneMeeting',
                                                                                 context=item.REQUEST))
                if 'comment' in advice and advice['comment'].strip():
                    res = res + (u"%s<br />" % unicode(advice['comment'].strip(), 'utf-8'))
        if itemAdvicesByType:
            res = res + u"</p>"
        if not itemAdvicesByType:
            return u"<p><u>%s : -</u></p>" % \
                translate('PloneMeeting_label_advices', domain='PloneMeeting', context=item.REQUEST).encode('utf-8')

        return res.encode('utf-8')

    security.declarePublic('getDecision')
    def getDecision(self, keepWithNext=False, **kwargs):
        '''Overridden version of 'decision' field accessor. It allows to specify
           p_keepWithNext=True. In that case, the last paragraph of bullet in
           field "decision" will get a specific CSS class that will keep it with
           next paragraph. Useful when including the decision in a document
           template and avoid having the signatures, just below it, being alone
           on the next page.
           Manage the 'add_published_state' workflowAdaptation that
           hides the decision for non-managers if meeting state is 'decided.'''
        item = self.getSelf()
        res = self.getField('decision').get(self, **kwargs)
        if keepWithNext:
            res = self.signatureNotAlone(res)
        meetingConfig = item.portal_plonemeeting.getMeetingConfig(item)
        adaptations = meetingConfig.getWorkflowAdaptations()
        if 'add_published_state' in adaptations and item.getMeeting() and \
           item.getMeeting().queryState() == 'decided' and not item.portal_plonemeeting.isManager():
            return translate('decision_under_edit', domain='PloneMeeting', context=item.REQUEST,
                             default='<p>The decision is currently under edit by managers, you can not access it</p>')
        return res
    MeetingItem.getDecision = getDecision
    MeetingItem.getRawDecision = getDecision

    security.declarePublic('customshowDuplicateItemAction')
    def customshowDuplicateItemAction(self):
        '''Condition for displaying the 'duplicate' action in the interface.
           Returns True if the user can duplicate the item.'''
        # Conditions for being able to see the "duplicate an item" action:
        # - the user is not Plone-disk-aware;
        # - the user is creator in some group;
        # - the user must be able to see the item if it is private.
        # The user will duplicate the item in his own folder.
        tool = self.portal_plonemeeting
        item = self.getSelf()
        ignoreDuplicateButton = item.queryState() == 'pre_accepted'
        if tool.getPloneDiskAware() or not tool.userIsAmong('creators') \
                or not self.isPrivacyViewable() or ignoreDuplicateButton:
            return False
        return True
    MeetingItem.showDuplicateItemAction = customshowDuplicateItemAction

    security.declarePublic('customclone')
    def customclone(self, copyAnnexes=True, newOwnerId=None, cloneEventAction=None,
                    destFolder=None, copyFields=DEFAULT_COPIED_FIELDS, newPortalType=None):
        '''Clones me in the PloneMeetingFolder of the current user, or
           p_newOwnerId if given (this guy will also become owner of this
           item). If there is a p_cloneEventAction, an event will be included
           in the cloned item's history, indicating that is was created from
           another item (useful for delayed items, but not when simply
           duplicating an item).  p_copyFields will contains a list of fields
           we want to keep value of, if not in this list, the new field value
           will be the default value for this field.'''
        # first check that we are not trying to clone an item the we
        # can not access because of privacy status
        item = self.getSelf()
        if not item.isPrivacyViewable():
            raise Unauthorized
        # Get the PloneMeetingFolder of the current user as destFolder
        tool = self.portal_plonemeeting
        userId = self.portal_membership.getAuthenticatedMember().getId()
        # Do not use "not destFolder" because destFolder is an ATBTreeFolder
        # and an empty ATBTreeFolder will return False while testing destFolder.
        if destFolder is None:
            meetingConfigId = tool.getMeetingConfig(item).getId()
            destFolder = tool.getPloneMeetingFolder(meetingConfigId, newOwnerId)
        # Copy/paste item into the folder
        sourceFolder = item.getParentNode()
        copiedData = sourceFolder.manage_copyObjects(ids=[item.id])
        # Check if an external plugin want to add some fieldsToCopy
        copyFields = copyFields + item.adapted().getExtraFieldsToCopyWhenCloning()
        res = tool.pasteItems(destFolder, copiedData, copyAnnexes=copyAnnexes,
                              newOwnerId=newOwnerId, copyFields=copyFields,
                              newPortalType=newPortalType)[0]
        #copy decision from source items in destination's deliberation if item is accepted
        if item.queryState() in ['accepted', 'accepted_but_modified']:
            res.setDescription(item.getDecision())
        #clear decision for new item
        res.setDecision('')
        if cloneEventAction:
            # We are sure that there is only one key in the workflow_history
            # because it was cleaned by ToolPloneMeeting.pasteItems.
            wfName = item.portal_workflow.getWorkflowsFor(res)[0].id
            firstEvent = res.workflow_history[wfName][0]
            cloneEvent = firstEvent.copy()
            cLabel = cloneEventAction + '_comments'
            cloneEvent['comments'] = translate(cLabel, domain='PloneMeeting', context=item.REQUEST)
            cloneEvent['action'] = cloneEventAction
            cloneEvent['actor'] = userId
            res.workflow_history[wfName] = (firstEvent, cloneEvent)
        # Call plugin-specific code when relevant
        res.adapted().onDuplicated(item)
        res.reindexObject()
        logger.info('Item at %s cloned (%s) by "%s" from %s.' %
                    (res.absolute_url_path(), cloneEventAction, userId,
                     item.absolute_url_path()))
        return res
    MeetingItem.clone = customclone


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
        pmtool = getToolByName(self, "portal_plonemeeting")
        # Get every Plone group related to a MeetingGroup
        for group in pmtool.getMeetingGroups(onlyActive=True):
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

    #we need to be able to give an advice in the initial_state
    from Products.PloneMeeting.MeetingConfig import MeetingConfig
    MeetingConfig.listItemStatesInitExcepted = MeetingConfig.listItemStates

    security.declarePublic('searchItemsToValidate')
    def searchItemsToValidate(self, sortKey, sortOrder, filterKey, filterValue, **kwargs):
        '''Return a list of items that the user can validate.
           Items to validated are items in state 'proposed' for wich the current user has the
           permission to trigger the 'validate' workflow transition.  To avoid waking up the
           object, we will check that the current user is in the _reviewers group corresponding
           to the item proposing group (that is indexed).  So if the item proposing group is
           'secretariat' and the user is member of 'secretariat_reviewers',
           then he is able to validate the item.'''
        member = self.portal_membership.getAuthenticatedMember()
        groupIds = self.portal_groups.getGroupsForPrincipal(member)
        res = []
        for groupId in groupIds:
            if groupId.endswith('_reviewers'):
                res.append(groupId[:-10])

        params = {'portal_type': self.getItemTypeName(),
                  'getProposingGroup': res,
                  'review_state': 'proposed',
                  'sort_on': sortKey,
                  'sort_order': sortOrder
                  }
        # Manage filter
        if filterKey:
            params[filterKey] = Keywords(filterValue).get()
        # update params with kwargs
        params.update(kwargs)
        # Perform the query in portal_catalog
        return self.portal_catalog(**params)
    MeetingConfig.searchItemsToValidate = searchItemsToValidate


class MeetingNamurCollegeWorkflowActions(MeetingWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingNamurCollegeWorkflowActions'''

    implements(IMeetingNamurCollegeWorkflowActions)
    security = ClassSecurityInfo()

    def _acceptEveryItems(self):
        """Helper method for accepting every items."""
        # Every item that is not decided will be automatically set to "accepted"
        for item in self.context.getAllItems():
            if item.queryState() == 'presented':
                self.context.portal_workflow.doActionFor(item, 'itemfreeze')
            if item.queryState() in ['itemfrozen', 'pre_accepted', ]:
                self.context.portal_workflow.doActionFor(item, 'accept')

    security.declarePrivate('doClose')
    def doClose(self, stateChange):
        '''Accept every items that are not still decided and manage
           first/last item number.'''
        self._acceptEveryItems()
        meetingConfig = self.context.portal_plonemeeting.getMeetingConfig(self.context)
        self.context.setFirstItemNumber(meetingConfig.getLastItemNumber()+1)
        # Update the item counter which is global to the meeting config
        meetingConfig.setLastItemNumber(meetingConfig.getLastItemNumber() +
                                        len(self.context.getItems()) +
                                        len(self.context.getLateItems()))

    security.declarePrivate('doDecide')
    def doDecide(self, stateChange):
        '''We pass every item that is 'presented' in the 'itemfrozen'
           state.  It is the case for late items. We initialize the decision
           field with content of Title+Description if no decision has already
           been written.'''
        empty_values = ('<p></p>', '<p> </p>', '<p><br></p>', '<p><br ></p>',
                        '<p><br /></p>', '<p><br/></p>', '<br>', '<br/>',
                        '<br />', '<br >')
        for item in self.context.getAllItems(ordered=True):
            if item.queryState() == 'presented':
                self.context.portal_workflow.doActionFor(item, 'itemfreeze')
            # If the decision field is empty, initialize it
            if not item.getDecision().strip() or \
               (item.getDecision().strip() in empty_values):
                item.setDecision("%s" % item.Description())
                item.reindexObject()

    security.declarePrivate('doPublish_decisions')
    def doPublish_decisions(self, stateChange):
        '''When the wfAdaptation 'add_published_state' is activated.'''
        self._acceptEveryItems()

    security.declarePrivate('doBackToCreated')
    def doBackToCreated(self, stateChange):
        '''When a meeting go back to the "created" state, for example the
           meeting manager wants to add an item, we do not do anything.'''
        pass

    security.declarePrivate('doBackToDecisionsPublished')
    def doBackToDecisionsPublished(self, stateChange):
        '''When the wfAdaptation 'add_published_state' is activated.'''
        pass


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
        if checkPermission(ReviewPortalContent, self.context) and \
           (not self._allItemsAreDelayed()):
            res = True
        return res

    def mayCorrect(self):
        '''Take the default behaviour except if the meeting is frozen
           we still have the permission to correct it.'''
        from Products.PloneMeeting.Meeting import MeetingWorkflowConditions
        res = MeetingWorkflowConditions.mayCorrect(self)
        currentState = self.context.queryState()
        if not res and (currentState in ("frozen", "decisions_published",)):
            # Change the behaviour for being able to correct a
            # frozen or decisions_published meeting
            if checkPermission(ReviewPortalContent, self.context):
                return True
        return res

    security.declarePublic('mayPublishDecisions')
    def mayPublishDecisions(self):
        '''Used when 'add_published_state' wfAdaptation is active.'''
        res = False
        # The user just needs the "Review portal content" permission on the
        # object to close it.
        if checkPermission(ReviewPortalContent, self.context):
            res = True
        return res


class MeetingItemNamurCollegeWorkflowActions(MeetingItemWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemNamurCollegeWorkflowActions'''

    implements(IMeetingItemNamurCollegeWorkflowActions)
    security = ClassSecurityInfo()

    security.declarePrivate('doPresent')
    def doPresent(self, stateChange):
        '''Manage what to do when we present an item in a meeting.'''
        meeting = getCurrentMeetingObject(self.context)
        meeting.insertItem(self.context)
        meetingState = meeting.queryState()
        wTool = self.context.portal_workflow
        if meetingState in ['frozen', 'decided', ]:
            # We are inserting an item in a frozen or decided meeting (probably
            # a late item ;-))
            # We need to freeze the item too...
            wTool.doActionFor(self.context, 'itemfreeze')

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
        empty_values = ('<p></p>', '<p> </p>', '<p><br></p>', '<p><br ></p>',
                        '<p><br /></p>', '<p><br/></p>', '<br>', '<br/>',
                        '<br />', '<br >')
        if not item.getDecision().strip() or \
           (item.getDecision().strip() in empty_values):
            item.setDecision("%s" % item.Description())
            item.reindexObject()

    security.declarePrivate('doAccept_but_modify')
    def doAccept_but_modify(self, stateChange):
        pass

    security.declarePrivate('doPre_accept')
    def doPre_accept(self, stateChange):
        pass

    security.declarePrivate('doCorrect')
    def doCorrect(self, stateChange):
        '''Suppress _budgetimpactreviewers role for this Item'''
        item = self.context
        #send mail to creator if item return to owner
        if item.queryState() == "itemcreated":
            recipients = (item.portal_membership.getMemberById(str(item.Creator())).getProperty('email'),)
            sendMail(recipients, item, "itemMustBeCorrected")
            # Clear the decision field if item going back to creator
            item.setDecision("")
        #we have to remove the item of the meeting
        if item.queryState() == "validated":
            # We may have to send a mail.
            item.sendMailIfRelevant('itemUnpresented', 'Owner', isRole=True)
            item.getMeeting().removeItem(item)
        #adapt MeetingBudgetImpactReviewerRole if needed
        item.adapted().giveMeetingBudgetImpactReviewerRole()

    security.declarePrivate('doDelay')
    def doDelay(self, stateChange):
        '''When an item is delayed, we will duplicate it: the copy is back to
           the initial state and will be linked to this one.
           After, we replace decision for initial items if needed'''
        DECISION_ERROR = 'There was an error in the TAL expression for defining the ' \
            'decision when an item is reported. Please check this in your meeting config. ' \
            'Original exception: %s'
        creator = self.context.Creator()
        # We create a copy in the initial item state, in the folder of creator.
        clonedItem = self.context.clone(copyAnnexes=True, newOwnerId=creator,
                                        cloneEventAction='create_from_predecessor')
        clonedItem.setPredecessor(self.context)
        clonedItem.setDecision('')
        # Send, if configured, a mail to the person who created the item
        clonedItem.sendMailIfRelevant('itemDelayed', 'Owner', isRole=True)
        # manage itemDecisionReportText
        meetingConfig = self.context.portal_plonemeeting.getMeetingConfig(self.context)
        itemDecisionReportText = meetingConfig.getRawItemDecisionReportText()
        if itemDecisionReportText.strip():
            from Products.CMFCore.Expression import Expression, createExprContext
            portal = self.context.portal_url.getPortalObject()
            ctx = createExprContext(self.context.getParentNode(), portal, self.context)
            try:
                res = Expression(itemDecisionReportText)(ctx)
            except Exception, e:
                self.context.plone_utils.addPortalMessage(PloneMeetingError(DECISION_ERROR % str(e)))
                return
            self.context.setDecision(res)

    security.declarePrivate('doRefuse')
    def doRefuse(self, stateChange):
        '''When an item is refused, the decision will be change'''
        meetingConfig = self.context.portal_plonemeeting.getMeetingConfig(self.context)
        itemDecisionRefuseText = meetingConfig.getItemDecisionRefuseText()
        if itemDecisionRefuseText.strip():
            from Products.CMFCore.Expression import Expression, createExprContext
            portal = self.context.portal_url.getPortalObject()
            ctx = createExprContext(self.context.getParentNode(), portal, self.context)
            try:
                res = Expression(itemDecisionRefuseText)(ctx)
            except Exception, e:
                self.context.portal_plonemeeting.plone_utils.addPortalMessage(PloneMeetingError(
                    DECISION_ERROR % str(e)))
                return
            self.context.setDecision(res)

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

    security.declarePublic('mayDelete')
    def mayDelete(self):
        '''
          By default it is not possible to delete an item if some
          decision annexes exist.  Here we do not care about this...
        '''
        return True

    security.declarePublic('mayDecide')
    def mayDecide(self):
        '''We may decide an item if the linked meeting is in relevant state.'''
        res = False
        meeting = self.context.getMeeting()
        if checkPermission(ReviewPortalContent, self.context) and \
           meeting and (meeting.queryState() in ['decided', 'closed', 'decisions_published', ]):
            res = True
        return res

    security.declarePublic('isLateFor')
    def isLateFor(self, meeting):
        res = False
        if meeting and (meeting.queryState() in ['frozen', 'decided']) and \
           (meeting.UID() == self.context.getPreferredMeeting()):
            itemValidationDate = self._getDateOfAction(self.context, 'validate')
            meetingFreezingDate = self._getDateOfAction(meeting, 'freeze')
            if itemValidationDate and meetingFreezingDate:
                if itemValidationDate > meetingFreezingDate:
                    res = True
        return res

    security.declarePublic('mayFreeze')
    def mayFreeze(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            if self.context.hasMeeting() and \
               (self.context.getMeeting().queryState() in ('frozen', 'decided', 'closed', 'decisions_published', )):
                res = True
        return res

    security.declarePublic('mayCorrect')
    def mayCorrect(self):
        # Check with the default PloneMeeting method and our test if res is
        # False. The diffence here is when we correct an item from itemfrozen to
        # presented, we have to check if the Meeting is in the "created" state
        # and not "published".
        res = MeetingItemWorkflowConditions.mayCorrect(self)
        # Item state
        currentState = self.context.queryState()
        # Manage our own behaviour now when the item is linked to a meeting,
        # a MeetingManager can correct anything except if the meeting is closed
        if not res and currentState in ['presented', 'itemfrozen', 'delayed',
                                        'refused', 'accepted', 'accepted_but_modified',
                                        'pre_accepted']:
            if checkPermission(ReviewPortalContent, self.context):
                # Get the meeting
                meeting = self.context.getMeeting()
                if meeting:
                    # Meeting can be None if there was a wf problem leading
                    # an item to be in a "presented" state with no linked
                    # meeting.
                    meetingState = meeting.queryState()
                    # A user having ReviewPortalContent permission can correct
                    # an item in any case except if the meeting is closed.
                    if meetingState != 'closed':
                        res = True
        return res


class MeetingNamurCouncilWorkflowActions(MeetingNamurCollegeWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingNamurCouncilWorkflowActions'''

    implements(IMeetingNamurCouncilWorkflowActions)
    security = ClassSecurityInfo()

    def _acceptEveryItems(self):
        """Helper method for accepting every items."""
        # Every item that is not decided will be automatically set to "accepted"
        # Every item that is "presented" will be automatically set to "accepted"
        for item in self.context.getAllItems():
            if item.queryState() == 'presented':
                self.context.portal_workflow.doActionFor(item, 'itemfreeze')
            if item.queryState() == 'itemfrozen':
                try:
                    self.context.portal_workflow.doActionFor(item, 'itempublish')
                except WorkflowException:
                    # in the case we selected the 'no_publication' wfAdaptation
                    # the itempublish transition does not exist anymore...
                    pass
            if item.queryState() in ('itemfrozen', 'itempublished', 'pre_accepted',):
                self.context.portal_workflow.doActionFor(item, 'accept')

    security.declarePrivate('doClose')
    def doClose(self, stateChange):
        '''Accept every items that are not still decided and manage
           first/last item number.'''
        self._acceptEveryItems()
        meetingConfig = self.context.portal_plonemeeting.getMeetingConfig(self.context)
        self.context.setFirstItemNumber(meetingConfig.getLastItemNumber()+1)
        # Update the item counter which is global to the meeting config
        meetingConfig.setLastItemNumber(meetingConfig.getLastItemNumber() +
                                        len(self.context.getItems()) +
                                        len(self.context.getLateItems()))

    security.declarePrivate('doDecide')
    def doDecide(self, stateChange):
        '''We pass every item that is 'presented' in the 'itemfrozen'
           state.  It is the case for late items. We initialize the decision
           field with content of Title+Description if no decision has already
           been written.'''
        empty_values = ('<p></p>', '<p> </p>', '<p><br></p>', '<p><br ></p>',
                        '<p><br /></p>', '<p><br/></p>', '<br>', '<br/>',
                        '<br />', '<br >')
        for item in self.context.getAllItems(ordered=True):
            if item.queryState() == 'presented':
                self.context.portal_workflow.doActionFor(item, 'itemfreeze')
            if item.queryState() == 'itemfrozen':
                try:
                    self.context.portal_workflow.doActionFor(item, 'itempublish')
                except WorkflowException:
                    # in the case we selected the 'no_publication' wfAdaptation
                    # the itempublish transition does not exist anymore...
                    pass
            # If the decision field is empty, initialize it
            if not item.getDecision().strip() or \
               (item.getDecision().strip() in empty_values):
                item.setDecision("<p>%s</p>%s" % (item.Title(),
                                                  item.Description()))
                item.reindexObject()

    security.declarePrivate('doPublish_decisions')
    def doPublish_decisions(self, stateChange):
        '''When the wfAdaptation 'add_published_state' is activated.'''
        self._acceptEveryItems()

    security.declarePrivate('doPublish')
    def doPublish(self, stateChange):
        '''When publishing the meeting, every items must be automatically set to
           "itempublished".'''
        for item in self.context.getAllItems(ordered=True):
            if item.queryState() == 'presented':
                self.context.portal_workflow.doActionFor(item, 'itemfreeze')
            if item.queryState() == 'itemfrozen':
                self.context.portal_workflow.doActionFor(item, 'itempublish')

    security.declarePrivate('doBackToDecisionsPublished')
    def doBackToDecisionsPublished(self, stateChange):
        '''When the wfAdaptation 'add_published_state' is activated.'''
        pass

    security.declarePrivate('doBackToPublished')
    def doBackToPublished(self, stateChange):
        '''We do not impact items while going back from decided.'''
        pass


class MeetingNamurCouncilWorkflowConditions(MeetingNamurCollegeWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingNamurCouncilWorkflowConditions'''

    implements(IMeetingNamurCouncilWorkflowConditions)
    security = ClassSecurityInfo()

    security.declarePublic('mayChangeItemsOrder')
    def mayChangeItemsOrder(self):
        '''We can change the order if :
           - the meeting state is in ('created', 'frozen', 'decided', )'''
        res = False
        if checkPermission(ModifyPortalContent, self.context) and \
           self.context.queryState() in ('created', 'frozen', 'decided'):
            res = True
        return res

    def mayCorrect(self):
        '''Take the default behaviour except if the meeting is frozen
           we still have the permission to correct it.'''
        from Products.PloneMeeting.Meeting import MeetingWorkflowConditions
        res = MeetingWorkflowConditions.mayCorrect(self)
        currentState = self.context.queryState()
        if not res and currentState in ['frozen', 'published', ]:
            # Change the behaviour for being able to correct a frozen meeting
            # back to created.
            if checkPermission(ReviewPortalContent, self.context):
                return True
        return res

    security.declarePublic('mayPublishDecisions')
    def mayPublishDecisions(self):
        '''Used when 'add_published_state' wfAdaptation is active.'''
        res = False
        # The user just needs the "Review portal content" permission on the
        # object to close it.
        if checkPermission(ReviewPortalContent, self.context):
            res = True
        return res


class MeetingItemNamurCouncilWorkflowActions(MeetingItemNamurCollegeWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemNamurCouncilWorkflowActions'''

    implements(IMeetingItemNamurCouncilWorkflowActions)
    security = ClassSecurityInfo()

    security.declarePrivate('doPresent')
    def doPresent(self, stateChange):
        '''Manage what to do when we present an item in a meeting.'''
        meeting = getCurrentMeetingObject(self.context)
        meeting.insertItem(self.context)
        meetingState = meeting.queryState()
        wTool = self.context.portal_workflow
        if meetingState == 'frozen':
            # We are inserting an item in a frozen meeting
            # We need to freeze the item too...
            wTool.doActionFor(self.context, 'itemfreeze')
        elif meetingState in ['published', 'decided']:
            # We are inserting an item in a published or decided meeting
            # We need to freeze and publish the item...
            wTool.doActionFor(self.context, 'itemfreeze')
            wTool.doActionFor(self.context, 'itempublish')


class MeetingItemNamurCouncilWorkflowConditions(MeetingItemNamurCollegeWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemNamurCouncilWorkflowConditions'''

    implements(IMeetingItemNamurCouncilWorkflowConditions)
    security = ClassSecurityInfo()

    security.declarePublic('isLateFor')
    def isLateFor(self, meeting):
        res = False
        if meeting and (meeting.queryState() in ['frozen', 'published', 'decided']) and \
           (meeting.UID() == self.context.getPreferredMeeting()):
            itemValidationDate = self._getDateOfAction(self.context, 'validate')
            meetingFreezingDate = self._getDateOfAction(meeting, 'freeze')
            if itemValidationDate and meetingFreezingDate:
                if itemValidationDate > meetingFreezingDate:
                    res = True
        return res

    security.declarePublic('mayDelete')
    def mayDelete(self):
        '''
          By default it is not possible to delete an item if some
          decision annexes exist.  Here we do not care about this...
        '''
        return True

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

    security.declarePublic('mayCorrect')
    def mayCorrect(self):
        # Check with the default PloneMeeting method and our test if res is
        # False. The diffence here is when we correct an item from itemfrozen to
        # presented, we have to check if the Meeting is in the "created" state
        # and not "published".
        res = MeetingItemWorkflowConditions.mayCorrect(self)
        # Item state
        currentState = self.context.queryState()
        # Manage our own behaviour now when the item is linked to a meeting,
        # a MeetingManager can correct anything except if the meeting is closed
        if not res and currentState in ['presented', 'itempublished', 'itemfrozen',
           'delayed', 'refused', 'accepted', 'accepted_but_modified', 'pre_accepted']:
            if checkPermission(ReviewPortalContent, self.context):
                # Get the meeting
                meeting = self.context.getMeeting()
                if meeting:
                    # Meeting can be None if there was a wf problem leading
                    # an item to be in a "presented" state with no linked
                    # meeting.
                    meetingState = meeting.queryState()
                    # A user having ReviewPortalContent permission can correct
                    # an item in any case except if the meeting is closed.
                    if meetingState != 'closed':
                        res = True
        return res

    security.declarePublic('mayDecide')
    def mayDecide(self):
        '''We may decide an item if the linked meeting is in relevant state.'''
        res = False
        meeting = self.context.getMeeting()
        if checkPermission(ReviewPortalContent, self.context) and \
           meeting and (meeting.queryState() in ('decided', 'closed', 'decisions_published',)):
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
InitializeClass(CustomMeetingItem)
InitializeClass(CustomMeeting)
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
