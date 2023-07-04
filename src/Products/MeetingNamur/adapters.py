# -*- coding: utf-8 -*-

from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from Products.MeetingNamur.config import WriteDecisionProject, WriteCertified
from Products.PloneMeeting.model.adaptations import WF_APPLIED, grantPermission
from collective.contact.plonegroup.utils import get_organizations
from imio.helpers.xhtml import xhtmlContentIsEmpty
from plone import api
from Products.Archetypes.atapi import DisplayList
from Products.CMFCore.utils import getToolByName
from Products.MeetingCommunes.adapters import CustomMeeting, CustomMeetingConfig
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
from Products.PloneMeeting.interfaces import IMeetingCustom, IMeetingConfigCustom
from Products.PloneMeeting.interfaces import IMeetingItemCustom
from Products.PloneMeeting.interfaces import IToolPloneMeetingCustom
from Products.PloneMeeting.Meeting import MeetingWorkflowActions
from Products.PloneMeeting.MeetingConfig import MeetingConfig
from Products.PloneMeeting.MeetingItem import MeetingItem
from Products.PloneMeeting.MeetingItem import MeetingItemWorkflowActions
from Products.PloneMeeting.utils import sendMail, org_id_to_uid
from zope.i18n import translate
from zope.interface import implements



customWfAdaptations = (
    'item_validation_shortcuts',
    'item_validation_no_validate_shortcuts',
    'only_creator_may_delete',
    # first define meeting workflow state removal
    'no_freeze',
    'no_publication',
    'no_decide',
    # then define added item decided states
    'accepted_but_modified',
    'postpone_next_meeting',
    'mark_not_applicable',
    'removed',
    'removed_and_duplicated',
    'refused',
    'delayed',
    'pre_accepted',
    # then other adaptations
    'reviewers_take_back_validated_item',
    'presented_item_back_to_validation_state',
    'return_to_proposing_group',
    'return_to_proposing_group_with_last_validation',
    'return_to_proposing_group_with_all_validations',
    'accepted_out_of_meeting',
    'accepted_out_of_meeting_and_duplicated',
    'accepted_out_of_meeting_emergency',
    'accepted_out_of_meeting_emergency_and_duplicated',
    'transfered',
    'transfered_and_duplicated',
    'meetingmanager_correct_closed_meeting',
    'namur_meetingmanager_may_not_edit_decision_project',
)
MeetingConfig.wfAdaptations = customWfAdaptations


class CustomNamurMeetingConfig(CustomMeetingConfig):
    implements(IMeetingConfigCustom)
    security = ClassSecurityInfo()

class CustomNamurMeeting(CustomMeeting):
    """Adapter that adapts a meeting implementing IMeeting to the
       interface IMeetingCustom."""

    implements(IMeetingCustom)
    security = ClassSecurityInfo()

    def __init__(self, meeting):
        self.context = meeting

    # Implements here methods that will be used by templates

    security.declarePublic('getPrintableItemsByCategory')

    def getPrintableItemsByCategory(self, itemUids=[], list_types=['normal'],
                                    ignore_review_states=[], by_proposing_group=False, group_prefixes={},
                                    privacy='*', oralQuestion='both', toDiscuss='both', categories=[],
                                    excludedCategories=[], groupIds=[], excludedGroupIds=[], group_proposing_group=True,
                                    firstNumber=1, renumber=False, additional_catalog_query={},
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

        items = self.context.get_items(uids=itemUids,
                                      list_types=list_types,
                                      ordered=True,
                                      additional_catalog_query=additional_catalog_query)

        if by_proposing_group:
            groups = get_organizations()
        else:
            groups = None
        if items:
            for item in items:
                # Check if the review_state has to be taken into account
                if item.query_state() in ignore_review_states:
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
                if group_proposing_group:
                    currentCat = item.getProposingGroup(theObject=True)
                else:
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
        if forceCategOrderFromConfig or cmp(list_types.sort(), ['late', 'normal']) == 0:
            res.sort(cmp=_comp)
        if includeEmptyCategories:
            meetingConfig = tool.getMeetingConfig(
                self.context)
            # onlySelectable = False will also return disabled categories...
            allCategories = [cat for cat in meetingConfig.getCategories(onlySelectable=False)
                             if cat.enabled]
            if "category" not in meetingConfig.getUsedItemAttributes():
                allCategories = get_organizations()

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



class CustomNamurMeetingItem(CustomMeetingItem):
    """Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCustom."""
    implements(IMeetingItemCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item


    security.declarePublic('print_scan_id_barcode')

    def print_scan_id_barcode(self, **kwargs):
        """Helper that will call scan_id_barcode from imio.zamqp.core
           and that will make sure that it is not called several times."""
        from imio.zamqp.core.utils import scan_id_barcode
        barcode = scan_id_barcode(self.context, **kwargs)
        return barcode

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

    security.declarePublic('updateMeetingBudgetImpactReviewerRole')

    def updateMeetingBudgetImpactReviewerRole(self):
        """Add MeetingBudgetImpactReviewer role when on an item, a group is choosen in BudgetInfosAdviser and state is,
           at least, "presented". Remove role for other grp_budgetimpactreviewers or remove all
           grp_budgetimpactreviewers in local role if state back in state before presented.
        """
        item = self.getSelf()
        grp_uids = []
        if item.query_state() in ('presented', 'itemfrozen', 'accepted', 'delayed', 'accepted_but_modified',
                                  'pre_accepted', 'refused'):
            # add new MeetingBudgetImpactReviewerRole
            for grpBudgetInfo in item.grpBudgetInfos:
                # for each group_budgetimpactreviewers add new local roles
                if grpBudgetInfo:
                    grp_role = '%s_budgetimpactreviewers' % grpBudgetInfo
                    grp_uid = org_id_to_uid(grp_role)
                    grp_uids.append(grp_uid)
                    item.manage_addLocalRoles(grp_uid, ('Reader', 'MeetingBudgetImpactReviewer',))
        # suppress old unused group_budgetimpactreviewers
        toRemove = []
        for user, roles in item.get_local_roles():
            if user.endswith('_budgetimpactreviewers') and user not in grp_uids:
                toRemove.append(user)
        item.manage_delLocalRoles(toRemove)

    def updateMeetingCertifiedSignaturesWriterLocalRoles(self):
        """
        Apply MeetingCertifiedSignaturesWriter local role so creators may edit the certified signature
        in item decided states
        """
        item = self.getSelf()
        cfg = item.portal_plonemeeting.getMeetingConfig(item)
        if item.query_state() in cfg.getItemPositiveDecidedStates():
            groupId = "{}_{}".format(item.getProposingGroup(), "creators")
            item.manage_addLocalRoles(groupId, ['MeetingCertifiedSignaturesWriter'])

    security.declareProtected('Modify portal content', 'onEdit')

    def onEdit(self, isCreated):
        item = self.getSelf()
        # adapt MeetingBudgetImpactReviewerRole if needed
        item.adapted().updateMeetingBudgetImpactReviewerRole()

    def _initDecisionFieldIfEmpty(self):
        """
          If decision field is empty, it will be initialized
          with data coming from title and decisionProject.
          Override for Namur !!!
        """
        # set keepWithNext to False as it will add a 'class' and so
        # xhtmlContentIsEmpty will never consider it empty...
        if xhtmlContentIsEmpty(self.getDecision(keepWithNext=False)):
            self.setDecision("%s" % self.getDecisionProject())
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
        ignoreDuplicateButton = item.query_state() == 'pre_accepted'
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
        state = item.query_state()
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
        for role in roles:
            if role not in ('Authenticated', 'Member', 'MeetingBudgetImpactReviewer', 'MeetingObserverGlobal', 'Reader'):
                return True
        return False

    def getExtraFieldsToCopyWhenCloning(self, cloned_to_same_mc, cloned_from_item_template):
        """
          Keep some new fields when item is cloned (to another mc or from itemtemplate).
        """
        res = ['grpBudgetInfos', 'itemCertifiedSignatures', 'isConfidentialItem', 'vote', 'decisionProject']
        if cloned_to_same_mc:
            res = res + []
        return res

    security.declarePublic('userCanView')

    def userCanView(self):
        """
        Helper method used in podtemplates to check if the current logged-in user
        can see the point in the document
        """
        item = self.getSelf()
        user = self.context.portal_membership.getAuthenticatedMember()
        userCanView = user.has_permission('View', item)
        return not item.getIsConfidentialItem() and userCanView


class MeetingNamurWorkflowActions(MeetingCommunesWorkflowActions):
    """Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingCommunesWorkflowActions"""

    implements(IMeetingNamurWorkflowActions)
    security = ClassSecurityInfo()


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
        if (item.query_state() == "itemcreated") or \
                (stateChange.old_state.id == "presented" and stateChange.new_state.id == "validated"):
            recipients = (item.portal_membership.getMemberById(str(item.Creator())).getProperty('email'),)
            sendMail(recipients, item, "itemMustBeCorrected")
            # Clear the decision field if item going back to service
            if item.query_state() == "itemcreated":
                item.setDecision("<p>&nbsp;</p>")
                item.reindexObject()
        if stateChange.old_state.id == "returned_to_proposing_group":
            # copy the description field into decision field
            item.setDecision("%s" % item.getDecisionProject())
            item.reindexObject()
        # adapt MeetingBudgetImpactReviewerRole if needed
        item.adapted().updateMeetingBudgetImpactReviewerRole()

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
        item.adapted().updateMeetingBudgetImpactReviewerRole()
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


    def performCustomWFAdaptations(
            self, meetingConfig, wfAdaptation, logger, itemWorkflow, meetingWorkflow
    ):
        """This function applies workflow changes as specified by the
        p_meetingConfig."""

        if wfAdaptation == "namur_meetingmanager_may_not_edit_decision_project":
            itemStates = itemWorkflow.states

            itemWorkflow.permissions = itemWorkflow.permissions + (WriteCertified, )
            creators_certified_sign_states = ["delayed", "accepted_but_modified", "accepted"]
            for state_id in itemStates:
                if state_id in creators_certified_sign_states:
                    itemStates[state_id].setPermission(WriteCertified, False, ["Manager", "Contributor"])
                else:
                    itemStates[state_id].setPermission(WriteCertified, False, ["Manager"])


            # First, we make sure that WriteDecisionProject perm is not acquired
            for state_id in itemStates:
                itemStates[state_id].setPermission(WriteDecisionProject, False, [])
            # Then, we set appropriate roles for the validationWF
            itemWorkflow.permissions = itemWorkflow.permissions + (WriteDecisionProject, )

            if "itemcreated" in itemStates:
                itemStates.itemcreated.setPermission(WriteDecisionProject, False, ["Manager", "Editor"])
            if "returned_to_proposing_group" in itemStates:
                itemStates["returned_to_proposing_group"].setPermission(WriteDecisionProject, False, ["Manager", "Editor"])

            for validation_level in meetingConfig.getItemWFValidationLevels():
                state_id = validation_level['state']
                if validation_level['enabled'] == '1' and state_id in itemStates:
                    itemStates[state_id].setPermission(WriteDecisionProject, False, ["Manager", "Editor"])
                # Handle returned_to_proposing_group
                returned_to_proposing_group_variant = "returned_to_proposing_group_{}".format(state_id)
                if returned_to_proposing_group_variant in itemStates:
                    itemStates[returned_to_proposing_group_variant].setPermission(WriteDecisionProject, False, ["Manager", "Editor"])
            logger.info(WF_APPLIED % ("namur_meetingmanager_may_not_edit_decision_project", meetingConfig.getId()))
            return True

        return False

# ------------------------------------------------------------------------------

InitializeClass(CustomNamurMeetingConfig)
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
