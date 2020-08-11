# -*- coding: utf-8 -*-
from copy import deepcopy
from Products.MeetingCommunes.profiles.testing import import_data as mc_import_data


data = deepcopy(mc_import_data.data)
# Meeting configurations -------------------------------------------------------
# College communal
collegeMeeting = deepcopy(mc_import_data.collegeMeeting)
collegeMeeting.itemWorkflow = 'meetingitemnamur_workflow'
collegeMeeting.meetingWorkflow = 'meetingnamur_workflow'
collegeMeeting.itemConditionsInterface = 'Products.MeetingNamur.interfaces.IMeetingItemNamurCollegeWorkflowConditions'
collegeMeeting.itemActionsInterface = 'Products.MeetingNamur.interfaces.IMeetingItemNamurCollegeWorkflowActions'
collegeMeeting.meetingConditionsInterface = 'Products.MeetingNamur.interfaces.IMeetingNamurCollegeWorkflowConditions'
collegeMeeting.meetingActionsInterface = 'Products.MeetingNamur.interfaces.IMeetingNamurCollegeWorkflowActions'
collegeMeeting.workflowAdaptations = []

# Conseil communal
councilMeeting = deepcopy(mc_import_data.councilMeeting)
councilMeeting.itemWorkflow = 'meetingitemnamur_workflow'
councilMeeting.meetingWorkflow = 'meetingnamur_workflow'
councilMeeting.itemConditionsInterface = 'Products.MeetingNamur.interfaces.IMeetingItemNamurCouncilWorkflowConditions'
councilMeeting.itemActionsInterface = 'Products.MeetingNamur.interfaces.IMeetingItemNamurCouncilWorkflowActions'
councilMeeting.meetingConditionsInterface = 'Products.MeetingNamur.interfaces.IMeetingNamurCouncilWorkflowConditions'
councilMeeting.meetingActionsInterface = 'Products.MeetingNamur.interfaces.IMeetingNamurCouncilWorkflowActions'
councilMeeting.workflowAdaptations = []
councilMeeting.itemCopyGroupsStates = []

data.meetingConfigs = (collegeMeeting, councilMeeting)

# ------------------------------------------------------------------------------
