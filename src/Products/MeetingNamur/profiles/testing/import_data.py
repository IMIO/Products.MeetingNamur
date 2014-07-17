# -*- coding: utf-8 -*-
from Products.PloneMeeting.profiles import *

# File types -------------------------------------------------------------------
annexe = MeetingFileTypeDescriptor('annexe', 'Annexe', 'attach.png', '')
annexeBudget = MeetingFileTypeDescriptor('annexeBudget', 'Article Budgetaire', 'budget.png', '')
annexeCahier = MeetingFileTypeDescriptor('annexeCahier', 'Cahier des Charges', 'cahier.gif', '')
annexeDecision = MeetingFileTypeDescriptor('annexeDecision', 'Annexe a la decision', 'attach.png', '', True)

# Categories -------------------------------------------------------------------
recurring = CategoryDescriptor('recurrents', 'Recurrents')
categories = [recurring,
              CategoryDescriptor('recurrents2', 'Recurrents2'),
              CategoryDescriptor('travaux', 'Travaux'),
              CategoryDescriptor('urbanisme', 'Urbanisme'),
              CategoryDescriptor('comptabilite', 'Comptabilite/Recettes'),
              CategoryDescriptor('personnel', 'Personnel'),
              CategoryDescriptor('population', 'Population/Etat-civil'),
              CategoryDescriptor('locations', 'Locations'),
              CategoryDescriptor('divers', 'Divers'),
             ]

# Users and groups -------------------------------------------------------------
pmManager = UserDescriptor('pmManager', ['MeetingManager'])
pmCreator1 = UserDescriptor('pmCreator1', [])
pmCreator1b = UserDescriptor('pmCreator1b', [])
pmReviewer1 = UserDescriptor('pmReviewer1', [])
pmCreator2 = UserDescriptor('pmCreator2', [])
pmReviewer2 = UserDescriptor('pmReviewer2', [])
pmAdviser1 = UserDescriptor('pmAdviser1', [])
pmTaxController = UserDescriptor('pmTaxController', ['MeetingTaxController'])
pmBudgetImpactReviewer = UserDescriptor('pmBudgetImpactReviewer', [])

developers = GroupDescriptor('developers', 'Developers', 'Devel', givesMandatoryAdviceOn="python:False")
developers.creators.append(pmCreator1)
developers.creators.append(pmCreator1b)
developers.creators.append(pmManager)
developers.reviewers.append(pmReviewer1)
developers.reviewers.append(pmManager)
developers.observers.append(pmReviewer1)
developers.observers.append(pmManager)
developers.advisers.append(pmAdviser1)
setattr(developers, 'signatures', 'developers signatures')
setattr(developers, 'echevinServices', 'developers')

#give an advice on recurring items
vendors = GroupDescriptor('vendors', 'Vendors', 'Devil', givesMandatoryAdviceOn="python: item.id == 'recurringagenda1'")
vendors.creators.append(pmCreator2)
vendors.reviewers.append(pmReviewer2)
vendors.observers.append(pmReviewer2)
vendors.advisers.append(pmReviewer2)
setattr(vendors, 'signatures', '')

finances = GroupDescriptor('finances', 'Finances', 'DGF', givesMandatoryAdviceOn="python:False")
finances.creators.append(pmTaxController)
finances.reviewers.append(pmTaxController)
finances.advisers.append(pmTaxController)
setattr(finances, 'pmBudgetImpactReviewer', pmBudgetImpactReviewer)

taxes = GroupDescriptor('taxes', 'Taxes', 'DGF-taxe', givesMandatoryAdviceOn="python:False")
taxes.creators.append(pmTaxController)
taxes.reviewers.append(pmTaxController)
taxes.advisers.append(pmTaxController)

# Meeting configurations -------------------------------------------------------
# college
collegeMeeting = MeetingConfigDescriptor(
    'meeting-config-college', 'College Communal',
    'College communal', isDefault=True)
collegeMeeting.assembly = 'Pierre Dupont - Bourgmestre,\n' \
                           'Charles Exemple - 1er Echevin,\n' \
                           'Echevin Un, Echevin Deux, Echevin Trois - Echevins,\n' \
                           'Jacqueline Exemple, Responsable du CPAS'
collegeMeeting.signatures = 'Pierre Dupont, Bourgmestre - Charles Exemple, 1er Echevin'
collegeMeeting.categories = categories
collegeMeeting.shortName = 'College'
collegeMeeting.meetingFileTypes = [annexe, annexeBudget, annexeCahier, annexeDecision]
collegeMeeting.itemWorkflow = 'meetingitemnamurcollege_workflow'
collegeMeeting.meetingWorkflow = 'meetingnamurcollege_workflow'
collegeMeeting.itemConditionsInterface = 'Products.MeetingNamur.interfaces.IMeetingItemNamurCollegeWorkflowConditions'
collegeMeeting.itemActionsInterface = 'Products.MeetingNamur.interfaces.IMeetingItemNamurCollegeWorkflowActions'
collegeMeeting.meetingConditionsInterface = 'Products.MeetingNamur.interfaces.IMeetingNamurCollegeWorkflowConditions'
collegeMeeting.meetingActionsInterface = 'Products.MeetingNamur.interfaces.IMeetingNamurCollegeWorkflowActions'
collegeMeeting.transitionsToConfirm = []
collegeMeeting.itemTopicStates = ('itemcreated', 'proposed', 'validated', 'presented', 'accepted', 'refused', 'delayed')
collegeMeeting.meetingTopicStates = ('created', 'frozen')
collegeMeeting.decisionTopicStates = ('decided', 'closed')
collegeMeeting.itemAdviceStates = ('validated',)
collegeMeeting.recordItemHistoryStates = []
collegeMeeting.maxShownMeetings = 5
collegeMeeting.maxDaysDecisions = 60
collegeMeeting.meetingAppDefaultView = 'topic_searchmyitems'
collegeMeeting.itemDocFormats = ('odt', 'pdf')
collegeMeeting.meetingDocFormats = ('odt', 'pdf')
collegeMeeting.useAdvices = True
collegeMeeting.useCopies = True
collegeMeeting.selectableCopyGroups = [developers.getIdSuffixed('reviewers'), vendors.getIdSuffixed('reviewers'), finances.getIdSuffixed('reviewers'),]
collegeMeeting.meetingConfigsToCloneTo = ['meeting-config-council', ] 

collegeMeeting.recurringItems = [
    RecurringItemDescriptor(
        id='recurringagenda1',
        title='Approuve le procès-verbal de la séance antérieure',
        description='Approuve le procès-verbal de la séance antérieure',
        category='recurrents',
        proposingGroup='developers',
        decision='Procès-verbal approuvé'),
    RecurringItemDescriptor(
        id='recurringofficialreport1',
        title='Autorise et signe les bons de commande de la semaine',
        description='Autorise et signe les bons de commande de la semaine',
        category='recurrents',
        proposingGroup='developers',
        decision='Bons de commande signés'),
    RecurringItemDescriptor(
        id='recurringofficialreport2',
        title='Ordonnance et signe les mandats de paiement de la semaine',
        description='Ordonnance et signe les mandats de paiement de la semaine',
        category='recurrents',
        proposingGroup='developers',
        decision='Mandats de paiement de la semaine approuvés'),
    ]

# Conseil communal
councilMeeting = MeetingConfigDescriptor(
    'meeting-config-council', 'Conseil Communal',
    'Conseil Communal')
councilMeeting.assembly = 'Default assembly'
councilMeeting.signatures = 'Default signatures'
councilMeeting.categories = categories
councilMeeting.shortName = 'Council'
councilMeeting.meetingFileTypes = [annexe, annexeBudget, annexeCahier, annexeDecision]
councilMeeting.displayNavigation = True
councilMeeting.itemWorkflow = 'meetingitemnamurcouncil_workflow'
councilMeeting.meetingWorkflow = 'meetingnamurcouncil_workflow'
councilMeeting.itemConditionsInterface = 'Products.MeetingNamur.interfaces.IMeetingItemNamurCouncilWorkflowConditions'
councilMeeting.itemActionsInterface = 'Products.MeetingNamur.interfaces.IMeetingItemNamurCouncilWorkflowActions'
councilMeeting.meetingConditionsInterface = 'Products.MeetingNamur.interfaces.IMeetingNamurCouncilWorkflowConditions'
councilMeeting.meetingActionsInterface = 'Products.MeetingNamur.interfaces.IMeetingNamurCouncilWorkflowActions'
#show every items states
councilMeeting.transitionsToConfirm = []
councilMeeting.itemTopicStates = ('itemcreated', 'proposed', 'validated', 'presented', 'accepted', 'pre_accepted', 'accepted_but_modified', 'refused', 'delayed')
councilMeeting.meetingTopicStates = ('created', 'frozen', 'published')
councilMeeting.decisionTopicStates = ('decided', 'closed')
councilMeeting.itemAdviceStates = ('validated',)
councilMeeting.recordItemHistoryStates = []
councilMeeting.maxShownMeetings = 5
councilMeeting.maxDaysDecisions = 60
councilMeeting.meetingAppDefaultView = 'topic_searchmyitems'
councilMeeting.itemDocFormats = ('odt', 'pdf')
councilMeeting.meetingDocFormats = ('odt', 'pdf')
councilMeeting.sortingMethodOnAddItem = 'on_categories'
councilMeeting.useGroupsAsCategories = True
councilMeeting.useAdvices = True
councilMeeting.useCopies = True
councilMeeting.selectableCopyGroups = [developers.getIdSuffixed('reviewers'), vendors.getIdSuffixed('reviewers'), finances.getIdSuffixed('reviewers'),]

#no recurring items for this meetingConfig, only for tests !!!
#so we can test a meetingConfig with recurring items (college) and without (council)

data = PloneMeetingConfiguration(
           meetingFolderTitle='Mes seances',
           meetingConfigs=(collegeMeeting, councilMeeting),
           groups=(developers, vendors, finances, taxes))
data.unoEnabledPython='/usr/bin/python'
# ------------------------------------------------------------------------------
