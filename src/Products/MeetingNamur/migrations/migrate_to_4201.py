# -*- coding: utf-8 -*-
import re

from DateTime import DateTime
from collective.contact.plonegroup.utils import get_organizations
from Products.PloneMeeting.utils import org_id_to_uid
from plone import api
from Products.PloneMeeting.migrations import Migrator
import logging


logger = logging.getLogger('MeetingNamur')


class Migrate_To_4201(Migrator):

    def _migrate_grpBudgetInfos(self):
        """"""
        logger.info("Adapting items's grpBudgetInfos...")
        catalog = api.portal.get_tool("portal_catalog")
        brains = catalog(meta_type=["MeetingItem"])
        orgs = get_organizations(only_selected=False)
        orgs_ids = ["/".join([o.id for o in org.get_organizations_chain(1)]) for org in orgs]
        for brain in brains:
            item = brain.getObject()
            if hasattr(item, "grpBudgetInfos") and item.grpBudgetInfos:
                new_values = []
                for grpBudgetInfo in item.grpBudgetInfos:
                    if grpBudgetInfo == "":
                        continue
                    matching_ids = [id for id in orgs_ids if id == grpBudgetInfo or re.match(".*\/%s$" % grpBudgetInfo, id)]
                    if len(matching_ids) == 1:
                        grp_uid = org_id_to_uid(matching_ids[0])
                        new_values.append(grp_uid)
                    else:
                        raise LookupError("No perfect matching grpBudgetInfos group found for %s" % str(item.absolute_url()))

                item.setGrpBudgetInfos(new_values)

    def run(self,
            profile_name=u'profile-Products.MeetingNamur:default',
            extra_omitted=[]):
        self._migrate_grpBudgetInfos()
        logger.info('Done migrating to MeetingNamur 4201...')


# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function:

       1) Change MeetingConfig workflows to use meeting_workflow/meetingitem_workflow;
       2) Call PloneMeeting migration to 4200 and 4201;
       3) In _after_reinstall hook, adapt items and meetings workflow_history
          to reflect new defined workflow done in 1);
    '''
    migrator = Migrate_To_4201(context)
    migrator.run()
    migrator.finish()
