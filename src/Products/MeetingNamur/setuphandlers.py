# -*- coding: utf-8 -*-
#
# File: setuphandlers.py
#
# Copyright (c) 2017 by Imio.be
# Generator: ArchGenXML Version 2.7
#            http://plone.org/products/archgenxml
#
# GNU General Public License (GPL)
#

__author__ = """Andre Nuyens <andre@imio.be>"""
__docformat__ = 'plaintext'


import logging
logger = logging.getLogger('MeetingNamur: setuphandlers')
from Products.MeetingNamur.config import PROJECTNAME
from Products.MeetingNamur.config import DEPENDENCIES
import os
from Products.CMFCore.utils import getToolByName
import transaction
##code-section HEAD
from Products.PloneMeeting.exportimport.content import ToolInitializer
from Products.PloneMeeting.model.adaptations import performWorkflowAdaptations
##/code-section HEAD

def isNotMeetingNamurProfile(context):
    return context.readDataFile("MeetingNamur_marker.txt") is None



def updateRoleMappings(context):
    """after workflow changed update the roles mapping. this is like pressing
    the button 'Update Security Setting' and portal_workflow"""
    if isNotMeetingNamurProfile(context): return
    wft = getToolByName(context.getSite(), 'portal_workflow')
    wft.updateRoleMappings()

def postInstall(context):
    """Called as at the end of the setup process. """
    # the right place for your custom code
    if isNotMeetingNamurProfile(context):
        return
    logStep("postInstall", context)
    site = context.getSite()
    #need to reinstall PloneMeeting after reinstalling MC workflows to re-apply wfAdaptations
    reinstallPloneMeeting(context, site)
    showHomeTab(context, site)
    reorderSkinsLayers(context, site)



##code-section FOOT
def logStep(method, context):
    logger.info("Applying '%s' in profile '%s'" %
                (method, '/'.join(context._profile_path.split(os.sep)[-3:])))


def isMeetingNamurConfigureProfile(context):
    return context.readDataFile("MeetingNamur_examples_fr_marker.txt") or \
        context.readDataFile("MeetingNamur_tests_marker.txt")


def isMeetingNamurTestingProfile(context):
    return context.readDataFile("MeetingNamur_tests_marker.txt")


def isMeetingNamurMigrationProfile(context):
    return context.readDataFile("MeetingNamur_migrations_marker.txt")


def installMeetingNamur(context):
    """ Run the default profile"""
    if not isMeetingNamurConfigureProfile(context):
        return
    logStep("installMeetingNamur", context)
    portal = context.getSite()
    portal.portal_setup.runAllImportStepsFromProfile('profile-Products.MeetingNamur:default')


def initializeTool(context):
    '''Initialises the PloneMeeting tool based on information from the current
       profile.'''
    if not isMeetingNamurConfigureProfile(context):
        return

    logStep("initializeTool", context)
    #PloneMeeting is no more a dependency to avoid
    #magic between quickinstaller and portal_setup
    #so install it manually
    _installPloneMeeting(context)
    return ToolInitializer(context, PROJECTNAME).run()


def reinstallPloneMeeting(context, site):
    '''Reinstall PloneMeeting so after install methods are called and applied,
       like performWorkflowAdaptations for example.'''

    if isNotMeetingNamurProfile(context):
        return

    logStep("reinstallPloneMeeting", context)
    _installPloneMeeting(context)


def _installPloneMeeting(context):
    site = context.getSite()
    profileId = u'profile-Products.PloneMeeting:default'
    site.portal_setup.runAllImportStepsFromProfile(profileId)


def showHomeTab(context, site):
    """
       Make sure the 'home' tab is shown...
    """
    if isNotMeetingNamurProfile(context):
        return

    logStep("showHomeTab", context)

    index_html = getattr(site.portal_actions.portal_tabs, 'index_html', None)
    if index_html:
        index_html.visible = True
    else:
        logger.info("The 'Home' tab does not exist !!!")


def reorderSkinsLayers(context, site):
    """
       Re-apply MeetingNamur skins.xml step
       as the reinstallation of MeetingNamur and PloneMeeting changes the portal_skins layers order
    """
    if isNotMeetingNamurProfile(context) and not isMeetingNamurConfigureProfile:
        return

    logStep("reorderSkinsLayers", context)
    site.portal_setup.runImportStepFromProfile(u'profile-Products.MeetingNamur:default', 'skins')


def addTaxControllerGroup(context):
    """
      Add a Plone group configured to receive MeetingTaxController
      These users can modify the items since they are frozen
      This group recieved the MeetingPowerObserverRôle
    """
    if isNotMeetingNamurProfile(context):
        return
    logStep("addTaxControllerGroup", context)
    portal = context.getSite()
    groupId = "meetingtaxcontroller"
    if not groupId in portal.portal_groups.listGroupIds():
        portal.portal_groups.addGroup(groupId,
                                      title=portal.utranslate("taxControllerGroupTitle", domain='PloneMeeting'))
        portal.portal_groups.setRolesForGroup(groupId, ('MeetingObserverGlobal', 'MeetingPowerObserverLocal',
                                                        'MeetingTaxController'))


def finalizeExampleInstance(context):
    """
       Some parameters can not be handled by the PloneMeeting installation,
       so we handle this here
    """
    if not isMeetingNamurConfigureProfile(context):
        return

    # finalizeExampleInstance on namur instance
    meetingConfig1Id = 'meeting-config-college'
    meetingConfig2Id = 'meeting-config-council'

    site = context.getSite()

    logStep("finalizeExampleInstance", context)
    # add the test users 'dfin' and 'bourgmestre' to every '_powerobservers' groups
    for memberId in ('dfin', 'bourgmestre', ):
        member = site.portal_membership.getMemberById(memberId)
        if member:
            site.portal_groups.addPrincipalToGroup(member.getId(), '%s_powerobservers' % meetingConfig1Id)
            site.portal_groups.addPrincipalToGroup(member.getId(), '%s_powerobservers' % meetingConfig2Id)
    # add the test user 'conseiller' only to the 'meeting-config-council_powerobservers' group

    member = site.portal_membership.getMemberById('conseiller')
    if member:
        site.portal_groups.addPrincipalToGroup(member.getId(), '%s_powerobservers' % meetingConfig2Id)

    # add the test user 'dfin' and 'chefCompta' to the 'meeting-config-xxx_budgetimpacteditors' groups
    for memberId in ('dfin', 'chefCompta', ):
        member = site.portal_membership.getMemberById(memberId)
        if member:
            site.portal_groups.addPrincipalToGroup(memberId, '%s_budgetimpacteditors' % meetingConfig1Id)
            site.portal_groups.addPrincipalToGroup(memberId, '%s_budgetimpacteditors' % meetingConfig2Id)

    # add some extra topics to each MeetingConfig
    topicsInfo = (
        # Items in state 'proposed'
        ('searchproposeditems',
         (('portal_type', 'ATPortalTypeCriterion', ('MeetingItem',)),
          ('review_state', 'ATListCriterion', ('proposed',),)
          ),
         'created',
         '',
         "python: not here.portal_plonemeeting.userIsAmong('reviewers')",
         ),
        # Items in state 'validated'
        ('searchvalidateditems',
         (('portal_type', 'ATPortalTypeCriterion', ('MeetingItem',)),
         ('review_state', 'ATListCriterion', ('validated',),)
          ),
         'created',
         '',
         '',
         ),
        # Items for cdld synthesis
        ('searchcdlditems',
        (('Type', 'ATPortalTypeCriterion', ('MeetingItem',)),
         ),
        'created',
        'searchCDLDItems',
        "python: '%s_budgetimpacteditors' % here.portal_plonemeeting.getMeetingConfig(here)"
        ".getId() in member.getGroups() or here.portal_plonemeeting.isManager(here)", ),
    )
    mc_college = getattr(site.portal_plonemeeting, meetingConfig1Id)
    mc_college.createTopics(topicsInfo)
    mc_council = getattr(site.portal_plonemeeting, meetingConfig2Id)
    mc_council.createTopics(topicsInfo)

    # add some topics to the portlet_todo
    mc_college.setToDoListTopics(
        [getattr(mc_college.topics, 'searchdecideditems'),
         getattr(mc_college.topics, 'searchallitemsincopy'),
         getattr(mc_college.topics, 'searchitemstoadvicewithdelay'),
         getattr(mc_college.topics, 'searchallitemstoadvice'),
         ])
    # add some topics to the portlet_todo
    mc_council.setToDoListTopics(
        [getattr(mc_council.topics, 'searchdecideditems'),
         getattr(mc_council.topics, 'searchallitemsincopy'),
         ])

    # finally, re-launch plonemeetingskin and MeetingNamur skins step
    # because PM has been installed before the import_data profile and messed up skins layers
    site.portal_setup.runImportStepFromProfile(u'profile-Products.MeetingNamur:default', 'skins')
    # define default workflowAdaptations for council
    # due to some weird problems, the wfAdaptations can not be defined
    # thru the import_data...
    mc_council.setWorkflowAdaptations(['no_global_observation', 'no_publication'])
    performWorkflowAdaptations(site, mc_council, logger)


def reorderCss(context):
    """
       Make sure CSS are correctly reordered in portal_css so things
       work as expected...
    """
    if isNotMeetingNamurProfile(context) and not isMeetingNamurConfigureProfile(context):
        return

    site = context.getSite()

    logStep("reorderCss", context)

    portal_css = site.portal_css
    css = ['plonemeeting.css',
           'meeting.css',
           'meetingitem.css',
           'meetingnamur.css',
           'imioapps.css',
           'plonemeetingskin.css',
           'imioapps_IEFixes.css',
           'ploneCustom.css']
    for resource in css:
        portal_css.moveResourceToBottom(resource)

##/code-section FOOT
