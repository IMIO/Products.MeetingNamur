# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger('MeetingNamur')

from plone import api

from Products.PloneMeeting.migrations.migrate_to_4_0 import Migrate_To_4_0 as PMMigrate_To_4_0


# The migration class ----------------------------------------------------------
class Migrate_To_4_0(PMMigrate_To_4_0):

    wfs_to_delete = []

    def _cleanCDLD(self):
        """We removed things related to 'CDLD' finance advice, so:
           - remove the 'cdld-document-generate' from document_actions;
           - remove the MeetingConfig.CdldProposingGroup attribute.
        """
        logger.info('Removing CDLD related things...')
        doc_actions = self.portal.portal_actions.document_actions
        # remove the action from document_actions
        if 'cdld-document-generate' in doc_actions:
            doc_actions.manage_delObjects(ids=['cdld-document-generate', ])
        # clean the MeetingConfigs
        for cfg in self.tool.objectValues('MeetingConfig'):
            if hasattr(cfg, 'cdldProposingGroup'):
                delattr(cfg, 'cdldProposingGroup')
        logger.info('Done.')

    def _migrateItemPositiveDecidedStates(self):
        """Before, the states in which an item was auto sent to
           selected other meetingConfig was defined in a method
           'itemPositiveDecidedStates' now it is stored in MeetingConfig.itemAutoSentToOtherMCStates.
           We store these states in the MeetingConfig.itemPositiveDecidedStates, it is used
           to display the 'sent from' leading icon on items sent from another MeetingConfig."""
        logger.info('Defining values for MeetingConfig.itemAutoSentToOtherMCStates...')
        for cfg in self.tool.objectValues('MeetingConfig'):
            cfg.setItemAutoSentToOtherMCStates(('accepted', 'accepted_but_modified', ))
            cfg.setItemPositiveDecidedStates(('accepted', 'accepted_but_modified', ))
        logger.info('Done.')

    def _after_reinstall(self):
        """Use that hook that is called just after the profile has been reinstalled by
           PloneMeeting, this way, we may launch some steps before PloneMeeting ones.
           Here we will update used workflows before letting PM do his job."""
        logger.info('Replacing old no more existing workflows...')
        PMMigrate_To_4_0._after_reinstall(self)
        for cfg in self.tool.objectValues('MeetingConfig'):
            # MeetingItem workflow
            if cfg.getItemWorkflow() == 'meetingitemnamurcollege_workflow':
                cfg.setItemWorkflow('meetingitemnamur_workflow')
                cfg._v_oldItemWorkflow = 'meetingitemnamurcollege_workflow'
                wfAdaptations = list(cfg.getWorkflowAdaptations())
                cfg.setWorkflowAdaptations(wfAdaptations)
            if cfg.getItemWorkflow() == 'meetingitemnamurcouncil_workflow':
                cfg.setItemWorkflow('meetingitemnamur_workflow')
                cfg._v_oldItemWorkflow = 'meetingitemnamurcouncil_workflow'
            # Meeting workflow
            if cfg.getMeetingWorkflow() == 'meetingnamurcollege_workflow':
                cfg.setMeetingWorkflow('meetingnamur_workflow')
                cfg._v_oldMeetingWorkflow = 'meetingnamurcollege_workflow'
            if cfg.getMeetingWorkflow() == 'meetingnamurcouncil_workflow':
                cfg.setMeetingWorkflow('meetingnamur_workflow')
                cfg._v_oldMeetingWorkflow = 'meetingnamurcouncil_workflow'
        # delete old unused workflows, aka every workflows containing 'college' or 'council'
        wfTool = api.portal.get_tool('portal_workflow')
        self.wfs_to_delete = [wfId for wfId in wfTool.listWorkflows()
                              if wfId.endswith(('meetingitemnamurcollege_workflow',
                                                'meetingitemnamurcouncil_workflow',
                                                'meetingnamurcollege_workflow',
                                                'meetingnamurcouncil_workflow'))]
        logger.info('Done.')

    def _deleteUselessWorkflows(self):
        """Finally, remove useless workflows."""
        logger.info('Removing useless workflows...')
        if self.wfs_to_delete:
            wfTool = api.portal.get_tool('portal_workflow')
            wfTool.manage_delObjects(self.wfs_to_delete)
        logger.info('Done.')

    def run(self):
        # change self.profile_name that is reinstalled at the beginning of the PM migration
        self.profile_name = u'profile-Products.MeetingNamur:default'
        # call steps from Products.PloneMeeting
        PMMigrate_To_4_0.run(self)
        # now MeetingLiege specific steps
        logger.info('Migrating to MeetingNamur 4.0...')
        self._cleanCDLD()
        self._migrateItemPositiveDecidedStates()
        self._deleteUselessWorkflows()


# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function:

       1) Reinstall Products.MeetingNamur and execute the Products.PloneMeeting migration;
       2) Clean CDLD attributes;
       3) Migrate positive decided states.
    '''
    migrator = Migrate_To_4_0(context)
    migrator.run()
    migrator.finish()
# ------------------------------------------------------------------------------
