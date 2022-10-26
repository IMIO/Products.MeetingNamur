# -*- coding: utf-8 -*-
from copy import deepcopy
from Products.MeetingCommunes.profiles.testing import import_data as mc_import_data


data = deepcopy(mc_import_data.data)

# Meeting configurations -------------------------------------------------------
# College communal
collegeMeeting = deepcopy(mc_import_data.collegeMeeting)
collegeMeeting.workflowAdaptations = ['no_publication', 'pre_accepted', 'accepted_but_modified', 'delayed', 'refused']
collegeMeeting.itemConditionsInterface = 'Products.MeetingNamur.interfaces.IMeetingItemNamurCollegeWorkflowConditions'
collegeMeeting.itemActionsInterface = 'Products.MeetingNamur.interfaces.IMeetingItemNamurCollegeWorkflowActions'
collegeMeeting.meetingConditionsInterface = 'Products.MeetingNamur.interfaces.IMeetingNamurCollegeWorkflowConditions'
collegeMeeting.meetingActionsInterface = 'Products.MeetingNamur.interfaces.IMeetingNamurCollegeWorkflowActions'

# Conseil communal
councilMeeting = deepcopy(mc_import_data.councilMeeting)
councilMeeting.workflowAdaptations = ['delayed', 'no_publication']
councilMeeting.itemConditionsInterface = 'Products.MeetingNamur.interfaces.IMeetingItemNamurCouncilWorkflowConditions'
councilMeeting.itemActionsInterface = 'Products.MeetingNamur.interfaces.IMeetingItemNamurCouncilWorkflowActions'
councilMeeting.meetingConditionsInterface = 'Products.MeetingNamur.interfaces.IMeetingNamurCouncilWorkflowConditions'
councilMeeting.itemCopyGroupsStates = []

data.meetingConfigs = (collegeMeeting, councilMeeting)

# ------------------------------------------------------------------------------
