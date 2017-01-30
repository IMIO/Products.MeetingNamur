# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger('PloneMeeting')

from Products.PloneMeeting.utils import forceHTMLContentTypeForEmptyRichFields
from Products.PloneMeeting.migrations import Migrator


# The migration class ----------------------------------------------------------
class Migrate_To_3_3_2(Migrator):

    def _initNewHTMLFields(self):
        '''The MeetingItem and Meeting receive to new HTML fields 'notes' and 'inAndOutMoves',
           make sure the content_type is correctly set to 'text/html'.
           It also manage new field Meeting.authorityNotice.'''
        logger.info('Initializing new HTML fields on meeting and items...')
        brains = self.portal.portal_catalog(meta_type=('Meeting', 'MeetingItem', ))
        for brain in brains:
            itemOrMeeting = brain.getObject()
            forceHTMLContentTypeForEmptyRichFields(itemOrMeeting)
        logger.info('Done.')

    def run(self):
        logger.info('Migrating to MeetingCommunes 3.3.2...')
        self._initNewHTMLFields()
        self.finish()


# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function:

       1) Init new html field;
    '''
    Migrate_To_3_3_2(context).run()
# ------------------------------------------------------------------------------
