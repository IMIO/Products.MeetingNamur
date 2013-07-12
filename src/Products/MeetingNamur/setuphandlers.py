# -*- coding: utf-8 -*-
#
# File: setuphandlers.py
#
# Copyright (c) 2013 by CommunesPlone
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
from DateTime import DateTime
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
    reinstallPloneMeetingSkin(context, site)



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


def reinstallPloneMeetingSkin(context, site):
    """
       Reinstall Products.plonemeetingskin as the reinstallation of MeetingNamur
       change the portal_skins layers order
    """
    if isNotMeetingNamurProfile(context) and not isMeetingNamurConfigureProfile:
        return

    logStep("reinstallPloneMeetingSkin", context)
    try:
        site.portal_setup.runAllImportStepsFromProfile(u'profile-plonetheme.imioapps:default')
        site.portal_setup.runAllImportStepsFromProfile(u'profile-plonetheme.imioapps:plonemeetingskin')
    except KeyError:
        # if the Products.plonemeetingskin profile is not available
        # (not using plonemeetingskin or in testing?) we pass...
        pass


def finalizeExampleInstance(context):
    """
       Some parameters can not be handled by the PloneMeeting installation,
       so we handle this here
    """
    if not isMeetingNamurConfigureProfile(context):
        return

    # finalizeExampleInstance on namur instance
    specialUserId = 'bourgmestre'
    meetingConfig1Id = 'meeting-config-college'
    meetingConfig2Id = 'meeting-config-council'

    site = context.getSite()

    logStep("finalizeExampleInstance", context)
    # add the test user 'bourgmestre' to every '_powerobservers' groups
    member = site.portal_membership.getMemberById(specialUserId)
    if member:
        site.portal_groups.addPrincipalToGroup(member.getId(), '%s_powerobservers' % meetingConfig1Id)
        site.portal_groups.addPrincipalToGroup(member.getId(), '%s_powerobservers' % meetingConfig2Id)
    # add the test user 'conseiller' to only the every 'meeting-config-council_powerobservers' groups
    member = site.portal_membership.getMemberById('conseiller')
    if member:
        site.portal_groups.addPrincipalToGroup(member.getId(), '%s_powerobservers' % meetingConfig2Id)

    # define some parameters for 'meeting-config-college'
    # items are sendable to the 'meeting-config-council'
    mc_college_or_bp = getattr(site.portal_plonemeeting, meetingConfig1Id)
    mc_college_or_bp.setMeetingConfigsToCloneTo([meetingConfig2Id, ])
    # add some topcis to the portlet_todo
    mc_college_or_bp.setToDoListTopics(
        [getattr(mc_college_or_bp.topics, 'searchdecideditems'),
         getattr(mc_college_or_bp.topics, 'searchitemstovalidate'),
         getattr(mc_college_or_bp.topics, 'searchallitemsincopy'),
         getattr(mc_college_or_bp.topics, 'searchallitemstoadvice'),
         ])
    # call updateCloneToOtherMCActions inter alia
    mc_college_or_bp.at_post_edit_script()

    # define some parameters for 'meeting-config-council'
    mc_council_or_cas = getattr(site.portal_plonemeeting, meetingConfig2Id)
    # add some topcis to the portlet_todo
    mc_council_or_cas.setToDoListTopics(
        [getattr(mc_council_or_cas.topics, 'searchdecideditems'),
         getattr(mc_council_or_cas.topics, 'searchitemstovalidate'),
         getattr(mc_council_or_cas.topics, 'searchallitemsincopy'),
         ])

    # finally, re-launch plonemeetingskin and MeetingNamur skins step
    # because PM has been installed before the import_data profile and messed up skins layers
    site.portal_setup.runImportStepFromProfile(u'profile-Products.MeetingNamur:default', 'skins')
    site.portal_setup.runImportStepFromProfile(u'profile-plonetheme.imioapps:default', 'skins')
    site.portal_setup.runImportStepFromProfile(u'profile-plonetheme.imioapps:plonemeetingskin', 'skins')
    # define default workflowAdaptations for council
    # due to some weird problems, the wfAdaptations can not be defined
    # thru the import_data...
    mc_council_or_cas.setWorkflowAdaptations(['no_global_observation', 'no_publication'])
    performWorkflowAdaptations(site, mc_council_or_cas, logger)


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
