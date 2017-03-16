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


import os
import logging
logger = logging.getLogger('MeetingCommunes: setuphandlers')
from plone import api
from Products.PloneMeeting.exportimport.content import ToolInitializer
from Products.MeetingNamur.config import PROJECTNAME



def isNotMeetingNamurProfile(context):
    return context.readDataFile("MeetingNamur_marker.txt") is None


def updateRoleMappings(context):
    """after workflow changed update the roles mapping. this is like pressing
    the button 'Update Security Setting' and portal_workflow"""
    if isNotMeetingNamurProfile(context):
        return
    wft = api.portal.get_tool('portal_workflow')
    wft.updateRoleMappings()


def postInstall(context):
    """Called as at the end of the setup process. """
    # the right place for your custom code
    if isNotMeetingNamurProfile(context):
        return
    logStep("postInstall", context)
    site = context.getSite()
    # need to reinstall PloneMeeting after reinstalling MC workflows to re-apply wfAdaptations
    reinstallPloneMeeting(context, site)
    showHomeTab(context, site)
    reorderSkinsLayers(context, site)


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
    # PloneMeeting is no more a dependency to avoid
    # magic between quickinstaller and portal_setup
    # so install it manually
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
    if groupId not in portal.portal_groups.listGroupIds():
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
    mTool = api.portal.get_tool('portal_membership')
    groupsTool = api.portal.get_tool('portal_groups')
    member = mTool.getMemberById('bourgmestre')
    for memberId in ('dfin', 'bourgmestre', ):
        member = mTool.getMemberById(memberId)
        if member:
            groupsTool.addPrincipalToGroup(member.getId(), '%s_powerobservers' % meetingConfig1Id)
            groupsTool.addPrincipalToGroup(member.getId(), '%s_powerobservers' % meetingConfig2Id)
    # add the test user 'conseiller' only to the 'meeting-config-council_powerobservers' group

    member = mTool.getMemberById('conseiller')
    if member:
        groupsTool.addPrincipalToGroup(member.getId(), '%s_powerobservers' % meetingConfig2Id)

    # add the test user 'dfin' and 'chefCompta' to the 'meeting-config-xxx_budgetimpacteditors' groups
    for memberId in ('dfin', 'chefCompta', ):
        member = mTool.getMemberById(memberId)
        if member:
            site.portal_groups.addPrincipalToGroup(memberId, '%s_budgetimpacteditors' % meetingConfig1Id)
            site.portal_groups.addPrincipalToGroup(memberId, '%s_budgetimpacteditors' % meetingConfig2Id)

    # add some topics to the portlet_todo
    mc_college = getattr(site.portal_plonemeeting, meetingConfig1Id)
    mc_college.setToDoListSearches(
        [getattr(mc_college.searches.searches_items, 'searchdecideditems'),
         getattr(mc_college.searches.searches_items, 'searchallitemsincopy'),
         getattr(mc_college.searches.searches_items, 'searchitemstoadvicewithdelay'),
         getattr(mc_college.searches.searches_items, 'searchallitemstoadvice'),
         ])

    # add some topics to the portlet_todo
    mc_council = getattr(site.portal_plonemeeting, meetingConfig2Id)
    mc_council.setToDoListSearches(
        [getattr(mc_council.searches.searches_items, 'searchdecideditems'),
         getattr(mc_council.searches.searches_items, 'searchallitemsincopy'),
         ])

    # finally, re-launch plonemeetingskin and MeetingNamur skins step
    # because PM has been installed before the import_data profile and messed up skins layers
    site.portal_setup.runImportStepFromProfile(u'profile-Products.MeetingNamur:default', 'skins')


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
    css = ['imio.dashboard.css',
           'plonemeeting.css',
           'meetingnamur.css',
           'imioapps.css',
           'plonemeetingskin.css',
           'imioapps_IEFixes.css',
           'ploneCustom.css']
    for resource in css:
        portal_css.moveResourceToBottom(resource)
