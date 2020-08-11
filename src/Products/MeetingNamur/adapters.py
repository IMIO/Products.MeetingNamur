# -*- coding: utf-8 -*-

from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from collective.contact.plonegroup.utils import get_organizations
from imio.helpers.xhtml import xhtmlContentIsEmpty
from plone import api
from Products.Archetypes.atapi import DisplayList
from Products.CMFCore.utils import getToolByName
from Products.MeetingCommunes.adapters import CustomMeeting
from Products.MeetingCommunes.adapters import CustomMeetingItem
from Products.MeetingCommunes.adapters import CustomToolPloneMeeting
from Products.MeetingCommunes.adapters import MeetingCommunesWorkflowActions
from Products.MeetingCommunes.adapters import MeetingCommunesWorkflowConditions
from Products.MeetingCommunes.adapters import MeetingItemCommunesWorkflowActions
from Products.MeetingCommunes.adapters import MeetingItemCommunesWorkflowConditions
from Products.MeetingNamur.interfaces import IMeetingItemNamurCollegeWorkflowActions
from Products.MeetingNamur.interfaces import IMeetingItemNamurCollegeWorkflowConditions
from Products.MeetingNamur.interfaces import IMeetingItemNamurCouncilWorkflowActions
from Products.MeetingNamur.interfaces import IMeetingItemNamurCouncilWorkflowConditions
from Products.MeetingNamur.interfaces import IMeetingItemNamurWorkflowActions
from Products.MeetingNamur.interfaces import IMeetingItemNamurWorkflowConditions
from Products.MeetingNamur.interfaces import IMeetingNamurCollegeWorkflowActions
from Products.MeetingNamur.interfaces import IMeetingNamurCollegeWorkflowConditions
from Products.MeetingNamur.interfaces import IMeetingNamurCouncilWorkflowActions
from Products.MeetingNamur.interfaces import IMeetingNamurCouncilWorkflowConditions
from Products.MeetingNamur.interfaces import IMeetingNamurWorkflowActions
from Products.MeetingNamur.interfaces import IMeetingNamurWorkflowConditions
from Products.PloneMeeting.adapters import ItemPrettyLinkAdapter
from Products.PloneMeeting.interfaces import IMeetingCustom
from Products.PloneMeeting.interfaces import IMeetingItemCustom
from Products.PloneMeeting.interfaces import IToolPloneMeetingCustom
from Products.PloneMeeting.Meeting import MeetingWorkflowActions
from Products.PloneMeeting.MeetingConfig import MeetingConfig
from Products.PloneMeeting.MeetingItem import MeetingItem
from Products.PloneMeeting.MeetingItem import MeetingItemWorkflowActions
from Products.PloneMeeting.model import adaptations
from Products.PloneMeeting.utils import sendMail
from zope.i18n import translate
from zope.interface import implements


# Names of available workflow adaptations.
customWfAdaptations = ('return_to_proposing_group', 'return_to_proposing_group_with_last_validation',
                       'return_to_proposing_group_with_all_validations')
MeetingConfig.wfAdaptations = customWfAdaptations
originalPerformWorkflowAdaptations = adaptations.performWorkflowAdaptations

RETURN_TO_PROPOSING_GROUP_CUSTOM_PERMISSIONS = {'meetingitemnamur_workflow':
                                                # view permissions
                                                   {'Access contents information':
                                                         ('Manager', 'MeetingManager', 'MeetingMember',
                                                          'MeetingTaxController',
                                                          'MeetingReviewer', 'MeetingObserverLocal', 'Reader',),
                                                     'View':
                                                         ('Manager', 'MeetingManager', 'MeetingMember',
                                                          'MeetingTaxController',
                                                          'MeetingReviewer', 'MeetingObserverLocal', 'Reader',),
                                                     'PloneMeeting: Read decision':
                                                         ('Manager', 'MeetingManager', 'MeetingMember',
                                                          'MeetingTaxController',
                                                          'MeetingReviewer', 'MeetingObserverLocal', 'Reader',),
                                                     'PloneMeeting: Read item observations':
                                                         ('Manager', 'MeetingManager', 'MeetingMember',
                                                          'MeetingTaxController',
                                                          'MeetingReviewer', 'MeetingObserverLocal', 'Reader',),
                                                     'PloneMeeting: Read budget infos':
                                                         ('Manager', 'MeetingManager', 'MeetingMember',
                                                          'MeetingTaxController',
                                                          'MeetingReviewer', 'MeetingObserverLocal', 'Reader',),
                                                     # edit permissions
                                                     'Modify portal content':
                                                         ('Manager', 'MeetingMember', 'MeetingManager',
                                                          'MeetingReviewer',),
                                                     'PloneMeeting: Write decision':
                                                         ('Manager',),
                                                     'Review portal content':
                                                         ('Manager', 'MeetingMember', 'MeetingManager',
                                                          'MeetingReviewer',),
                                                     'Add portal content':
                                                         ('Manager', 'MeetingMember', 'MeetingManager',
                                                          'MeetingReviewer',),
                                                     'PloneMeeting: Add annex':
                                                         ('Manager', 'MeetingMember', 'MeetingManager',
                                                          'MeetingReviewer',),
                                                     'PloneMeeting: Add annexDecision':
                                                         ('Manager', 'MeetingMember', 'MeetingManager',
                                                          'MeetingReviewer',),
                                                     'PloneMeeting: Write budget infos':
                                                         ('Manager', 'MeetingMember', 'MeetingReviewer',
                                                          'MeetingBudgetImpactEditor', 'MeetingManager',
                                                          'MeetingBudgetImpactReviewer',),
                                                     'MeetingNamur: Write description':
                                                         ('Manager', 'MeetingMember', 'MeetingManager',
                                                          'MeetingReviewer',),
                                                     # MeetingManagers edit permissions
                                                     'MeetingNamur: Write certified signatures':
                                                         ('Manager',),
                                                     'PloneMeeting: Write marginal notes':
                                                         ('Manager',),
                                                     'PloneMeeting: Write item MeetingManager reserved fields':
                                                         ('Manager', 'MeetingManager',),
                                                     'Delete objects':
                                                         ['Manager', ], }
                                                }

adaptations.RETURN_TO_PROPOSING_GROUP_CUSTOM_PERMISSIONS = RETURN_TO_PROPOSING_GROUP_CUSTOM_PERMISSIONS

RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE = {'meetingitemnamur_workflow': 'meetingitemnamur_workflow.itemcreated'}

adaptations.RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE = RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE


class CustomNamurMeeting(CustomMeeting):
    """Adapter that adapts a meeting implementing IMeeting to the
       interface IMeetingCustom."""

    implements(IMeetingCustom)
    security = ClassSecurityInfo()

    def __init__(self, meeting):
        self.context = meeting

    # Implements here methods that will be used by templates

    security.declarePublic('getPrintableItemsByCategory')

    def getPrintableItemsByCategory(self, itemUids=[], listTypes=['normal'],
                                    ignore_review_states=[], by_proposing_group=False, group_prefixes={},
                                    privacy='*', oralQuestion='both', toDiscuss='both', categories=[],
                                    excludedCategories=[], groupIds=[], excludedGroupIds=[],
                                    firstNumber=1, renumber=False,
                                    includeEmptyCategories=False, includeEmptyGroups=False,
                                    forceCategOrderFromConfig=False, allNoConfidentialItems=False):
        """Returns a list of (late or normal or both) items (depending on p_listTypes)
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
           In this case, the firstNumber value can be used."""

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
        tool = getToolByName(self.context, 'portal_plonemeeting')
        # Retrieve the list of items
        for elt in itemUids:
            if elt == '':
                itemUids.remove(elt)

        items = self.context.getItems(uids=itemUids, listTypes=listTypes, ordered=True)

        if by_proposing_group:
            groups = get_organizations()
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
                catList = ''
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
                             if cat.enabled]
            usedCategories = [elem[0] for elem in res]
            for cat in allCategories:
                if cat not in usedCategories:
                    # no empty service, we want only show department
                    if not hasattr(cat, 'acronym') or cat.get_acronym().find('-') > 0:
                        continue
                    else:
                        # no empty department
                        dpt_empty = True
                        for uc in usedCategories:
                            if uc.get_acronym().startswith(cat.get_acronym()):
                                dpt_empty = False
                                break
                        if dpt_empty:
                            continue
                    # Insert the category among used categories at the right place.
                    categoryInserted = False
                    i = 0
                    for obj in res:
                        try:
                            if not obj[0].get_acronym().startswith(cat.get_acronym()):
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

    security.declarePublic('getVotes')

    def getVotes(self):
        """Get all item with "votes" for a meeting in a list to print in template"""
        res = []
        for item in self.context.getAllItems(ordered=True):
            if item.getVote():
                res.append(item)
        return res


class CustomNamurMeetingItem(CustomMeetingItem):
    """Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCustom."""
    implements(IMeetingItemCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item

    security.declarePublic('listGrpBudgetInfosAdviser')

    def listGrpBudgetInfosAdviser(self):
        """Returns a list of groups that can be selected on an item to modify budgetInfos field.
        acronym group start with DGF"""
        res = []
        res.append(('', self.utranslate('make_a_choice', domain='PloneMeeting')))
        orgs = get_organizations(not_empty_suffix='budgetimpactreviewers')
        for group in orgs:
            res.append((group.id, group.getProperty('title')))
        return DisplayList(tuple(res))

    MeetingItem.listGrpBudgetInfosAdviser = listGrpBudgetInfosAdviser

    security.declarePublic('giveMeetingBudgetImpactReviewerRole')

    def giveMeetingBudgetImpactReviewerRole(self):
        """Add MeetingBudgetImpactReviewer role when on an item, a group is choosen in BudgetInfosAdviser and state is,
           at least, "presented". Remove role for other grp_budgetimpactreviewers or remove all
           grp_budgetimpactreviewers in local role if state back in state before presented.
        """
        item = self.getSelf()
        grp_roles = []
        if item.queryState() in ('presented', 'itemfrozen', 'accepted', 'delayed', 'accepted_but_modified',
                                 'pre_accepted', 'refused'):
            # add new MeetingBudgetImpactReviewerRole
            for grpBudgetInfo in item.grpBudgetInfos:
                grp_role = '%s_budgetimpactreviewers' % grpBudgetInfo
                # for each group_budgetimpactreviewers add new local roles
                if grpBudgetInfo:
                    grp_roles.append(grp_role)
                    item.manage_addLocalRoles(grp_role, ('Reader', 'MeetingBudgetImpactReviewer',))
        # suppress old unused group_budgetimpactreviewers
        toRemove = []
        for user, roles in item.get_local_roles():
            if user.endswith('_budgetimpactreviewers') and user not in grp_roles:
                toRemove.append(user)
        item.manage_delLocalRoles(toRemove)

    security.declareProtected('Modify portal content', 'onEdit')

    def onEdit(self, isCreated):
        item = self.getSelf()
        # adapt MeetingBudgetImpactReviewerRole if needed
        item.adapted().giveMeetingBudgetImpactReviewerRole()

    def _initDecisionFieldIfEmpty(self):
        """
          If decision field is empty, it will be initialized
          with data coming from title and description.
          Override for Namur !!!
        """
        # set keepWithNext to False as it will add a 'class' and so
        # xhtmlContentIsEmpty will never consider it empty...
        if xhtmlContentIsEmpty(self.getDecision(keepWithNext=False)):
            self.setDecision("%s" % self.Description())
            self.reindexObject()

    MeetingItem._initDecisionFieldIfEmpty = _initDecisionFieldIfEmpty

    security.declarePublic('customshowDuplicateItemAction')

    def customshowDuplicateItemAction(self):
        """Condition for displaying the 'duplicate' action in the interface.
           Returns True if the user can duplicate the item."""
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
        """
            In model : list of decisions, we must map some traductions
            accepted : approuved
            removed : removed
            delay : delay
            pre_accepted : /
            accepted_but_modified : Approved with a modification
        """
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
        """ Check if advice with delay from a certain p_groupId and with
            a row_id contained in p_rowIds is timed out.
        """
        item = self.getSelf()
        if item.getAdviceDataFor(item) and groupId in item.getAdviceDataFor(item):
            adviceRowId = self.getAdviceDataFor(item, groupId)['row_id']
        else:
            return False

        if not rowIds or adviceRowId in rowIds:
            return item._adviceDelayIsTimedOut(groupId)
        else:
            return False

    security.declarePublic('viewFullFieldInItemEdit')

    def viewFullFieldInItemEdit(self):
        """
            This method is used in MeetingItem_edit.cpt
        """
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

    def getExtraFieldsToCopyWhenCloning(self, cloned_to_same_mc, cloned_from_item_template):
        """
          Keep some new fields when item is cloned (to another mc or from itemtemplate).
        """
        res = ['grpBudgetInfos', 'itemCertifiedSignatures', 'isConfidentialItem', 'vote']
        if cloned_to_same_mc:
            res = res + []
        return res


class MeetingNamurWorkflowActions(MeetingCommunesWorkflowActions):
    """Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingCommunesWorkflowActions"""

    implements(IMeetingNamurWorkflowActions)
    security = ClassSecurityInfo()

    security.declarePrivate('doDecide')

    def doDecide(self, stateChange):
        """We pass every item that is 'presented' in the 'itemfrozen'
           state.  It is the case for late items. Moreover, if
           MeetingConfig.initItemDecisionIfEmptyOnDecide is True, we
           initialize the decision field with content of Title+Description
           if decision field is empty."""
        for item in self.context.getItems():
            # If deliberation (decision) is empty,
            # initialize it the decision field
            item._initDecisionFieldIfEmpty()

    security.declarePrivate('doBackToPublished')

    def doClose(self, stateChange):
        """We initialize the decision field with content of Title+Description
           if no decision has already been written."""
        MeetingWorkflowActions.doClose(self, stateChange)
        for item in self.context.getItems():
            # If the decision field is empty, initialize it
            item._initDecisionFieldIfEmpty()


class MeetingNamurCollegeWorkflowActions(MeetingNamurWorkflowActions):
    """inherit class"""
    implements(IMeetingNamurCollegeWorkflowActions)


class MeetingNamurCouncilWorkflowActions(MeetingNamurWorkflowActions):
    """inherit class"""
    implements(IMeetingNamurCouncilWorkflowActions)


class MeetingNamurWorkflowConditions(MeetingCommunesWorkflowConditions):
    """Adapter that adapts a meeting item implementing IMeetingItem to the
       interface MeetingCommunesWorkflowConditions"""

    implements(IMeetingNamurWorkflowConditions)
    security = ClassSecurityInfo()


class MeetingNamurCollegeWorkflowConditions(MeetingNamurWorkflowConditions):
    """inherit class"""
    implements(IMeetingNamurCollegeWorkflowConditions)


class MeetingNamurCouncilWorkflowConditions(MeetingNamurWorkflowConditions):
    """inherit class"""
    implements(IMeetingNamurCouncilWorkflowConditions)


class MeetingItemNamurWorkflowActions(MeetingItemCommunesWorkflowActions):
    """Adapter that adapts a meeting item implementing IMeetingItem to the
       interface MeetingItemCommunesWorkflowActions"""

    implements(IMeetingItemNamurWorkflowActions)
    security = ClassSecurityInfo()

    security.declarePrivate('doValidate')

    def doValidate(self, stateChange):
        MeetingItemWorkflowActions.doValidate(self, stateChange)
        item = self.context
        # If the decision field is empty, initialize it
        item._initDecisionFieldIfEmpty()

    security.declarePrivate('doPresent')

    def doPresent(self, stateChange):
        MeetingItemWorkflowActions.doPresent(self, stateChange)
        item = self.context
        # If the decision field is empty, initialize it
        item._initDecisionFieldIfEmpty()

    security.declarePrivate('doCorrect')

    def doCorrect(self, stateChange):
        """ If needed, suppress _budgetimpactreviewers role for this Item and
            clean decision field or copy description field in decision field."""
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
        """Cleaning decision field"""
        MeetingItemWorkflowActions.doReturn_to_proposing_group(self, stateChange)
        item = self.context
        item.setDecision("<p>&nbsp;</p>")
        item.reindexObject()

    security.declarePrivate('doItemFreeze')

    def doItemFreeze(self, stateChange):
        """When an item is frozen, we must add local role MeetingBudgetReviewer """
        item = self.context
        # adapt MeetingBudgetImpactReviewerRole if needed
        item.adapted().giveMeetingBudgetImpactReviewerRole()
        # If the decision field is empty, initialize it
        item._initDecisionFieldIfEmpty()


class MeetingItemNamurCollegeWorkflowActions(MeetingItemNamurWorkflowActions):
    """inherit class"""
    implements(IMeetingItemNamurCollegeWorkflowActions)


class MeetingItemNamurCouncilWorkflowActions(MeetingItemNamurWorkflowActions):
    """inherit class"""
    implements(IMeetingItemNamurCouncilWorkflowActions)


class MeetingItemNamurWorkflowConditions(MeetingItemCommunesWorkflowConditions):
    """Adapter that adapts a meeting item implementing IMeetingItem to the
       interface MeetingItemCommunesWorkflowConditions"""

    implements(IMeetingItemNamurWorkflowConditions)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item  # Implements IMeetingItem


class MeetingItemNamurCollegeWorkflowConditions(MeetingItemNamurWorkflowConditions):
    """inherit class"""
    implements(IMeetingItemNamurCollegeWorkflowConditions)


class MeetingItemNamurCouncilWorkflowConditions(MeetingItemNamurWorkflowConditions):
    """inherit class"""
    implements(IMeetingItemNamurCouncilWorkflowConditions)


class CustomNamurToolPloneMeeting(CustomToolPloneMeeting):
    """Adapter that adapts a tool implementing ToolPloneMeeting to the
       interface IToolPloneMeetingCustom"""

    implements(IToolPloneMeetingCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item


# ------------------------------------------------------------------------------

InitializeClass(CustomNamurMeeting)
InitializeClass(CustomNamurMeetingItem)
InitializeClass(MeetingNamurWorkflowActions)
InitializeClass(MeetingNamurWorkflowConditions)
InitializeClass(MeetingItemNamurWorkflowActions)
InitializeClass(MeetingItemNamurWorkflowConditions)
InitializeClass(CustomNamurToolPloneMeeting)


# ------------------------------------------------------------------------------

class MNAItemPrettyLinkAdapter(ItemPrettyLinkAdapter):
    """
      Override to take into account Meetingnamur use cases...
    """

    def _leadingIcons(self):
        """
          Manage icons to display before the icons managed by PrettyLink._icons.
        """
        # Default PM item icons
        icons = super(MNAItemPrettyLinkAdapter, self)._leadingIcons()

        if self.context.isDefinedInTool():
            return icons

        # add an icon if item is confidential
        if self.context.getIsConfidentialItem():
            icons.append(('isConfidentialYes.png',
                          translate('isConfidentialYes',
                                    domain="PloneMeeting",
                                    context=self.request)))
        return icons
