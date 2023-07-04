# -*- coding: utf-8 -*-

from copy import deepcopy
from Products.MeetingCommunes.profiles.examples_fr import import_data as mc_import_data


data = deepcopy(mc_import_data.data)

# Meeting configurations -------------------------------------------------------
# College communal
collegeMeeting = deepcopy(mc_import_data.collegeMeeting)
collegeMeeting.itemConditionsInterface = 'Products.MeetingNamur.interfaces.IMeetingItemNamurCollegeWorkflowConditions'
collegeMeeting.itemActionsInterface = 'Products.MeetingNamur.interfaces.IMeetingItemNamurCollegeWorkflowActions'
collegeMeeting.meetingConditionsInterface = 'Products.MeetingNamur.interfaces.IMeetingNamurCollegeWorkflowConditions'
collegeMeeting.meetingActionsInterface = 'Products.MeetingNamur.interfaces.IMeetingNamurCollegeWorkflowActions'
collegeMeeting.transitionsToConfirm = []
collegeMeeting.podTemplates = []

# Conseil communal
councilMeeting = deepcopy(mc_import_data.councilMeeting)
councilMeeting.itemConditionsInterface = 'Products.MeetingNamur.interfaces.IMeetingItemNamurCouncilWorkflowConditions'
councilMeeting.itemActionsInterface = 'Products.MeetingNamur.interfaces.IMeetingItemNamurCouncilWorkflowActions'
councilMeeting.meetingConditionsInterface = 'Products.MeetingNamur.interfaces.IMeetingNamurCouncilWorkflowConditions'
councilMeeting.meetingActionsInterface = 'Products.MeetingNamur.interfaces.IMeetingNamurCouncilWorkflowActions'
councilMeeting.itemCopyGroupsStates = []
councilMeeting.transitionsToConfirm = []
councilMeeting.podTemplates = []

data.meetingConfigs = (collegeMeeting, councilMeeting)
# ------------------------------------------------------------------------------
