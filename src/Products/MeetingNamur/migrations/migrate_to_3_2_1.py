# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger('PloneMeeting')

from Products.PloneMeeting.migrations import Migrator


# The migration class ----------------------------------------------------------
class Migrate_To_3_2_1(Migrator):

    def _setItemsInConfidentials(self):
        '''We must set confidential to on for all existing items.'''
        logger.info('set confidentials to on for all items')
        brains = self.portal.portal_catalog(meta_type=('MeetingItem', ))
        logger.info('Updating MeetingItem for %s MeetingItem objects...' % len(brains))
        for brain in brains:
            obj = brain.getObject()
            obj.setIsConfidentialItem(True)
            obj.reindexObject()
        logger.info('Done.')

    def run(self):
        logger.info('Migrating to MeetingNamur 3.2.1...')
        self._setItemsInConfidentials()
        # reinstall so skins and so on are correct
        self.reinstall(profiles=[u'profile-Products.MeetingNamur:default', ])
        self.finish()


# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function:

       1) All items must be confidentials
    '''
    Migrate_To_3_2_1(context).run()
# ------------------------------------------------------------------------------
