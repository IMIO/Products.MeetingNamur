# -*- coding: utf-8 -*-

from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from Products.MeetingNamur.config import WriteDecisionProject
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
from Products.PloneMeeting.utils import sendMail
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
        if item.query_state() in ('presented', 'itemfrozen', 'accepted', 'delayed', 'accepted_but_modified',
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

    def updateMeetingCertifiedSignaturesWriterLocalRoles(self):
        """
        Apply MeetingCertifiedSignaturesWriter local role so creators may edit the certified signature
        in item decided states
        """
        item = self.getSelf()
        cfg = item.portal_plonemeeting.getMeetingConfig(item)
        if item.query_state() in cfg.getItemDecidedStates():
            groupId = "{}_{}".format(item.getProposingGroup(), "creators")
            item.manage_addLocalRoles(groupId, ['MeetingCertifiedSignaturesWriter'])

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
