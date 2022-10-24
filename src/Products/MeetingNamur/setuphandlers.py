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


from plone import api
from Products.MeetingNamur.config import PROJECTNAME
from Products.PloneMeeting.exportimport.content import ToolInitializer

import logging
import os


logger = logging.getLogger('MeetingNamur: setuphandlers')


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
    _installPloneMeeting(context)
    return ToolInitializer(context, PROJECTNAME).run()


def reinstallPloneMeeting(context, site):
    '''Reinstall PloneMeeting so after install methods are called and applied,
       like performWorkflowAdaptations for example.'''

    if isNotMeetingNamurProfile(context):
        return

    logStep("reinstallPloneMeeting", context)
    _installPloneMeeting(context)
    # launch skins step for MeetingNamur so MeetingNamur skin layers are before PM ones
    site.portal_setup.runImportStepFromProfile('profile-Products.MeetingNamur:default', 'skins')


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
