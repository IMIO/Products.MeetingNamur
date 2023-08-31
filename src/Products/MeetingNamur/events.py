# -*- coding: utf-8 -*-
#
# GNU General Public License (GPL)
#

from Products.PloneMeeting.utils import forceHTMLContentTypeForEmptyRichFields


def onItemLocalRolesUpdated(item, event):
    """Called after localRoles have been updated on the item."""
    item.adapted().updateMeetingBudgetImpactReviewerRole()
    item.adapted().updateMeetingCertifiedSignaturesWriterLocalRoles()


def onItemDuplicated(original, event):
    """After item's cloning, we copy in decisionProject field the decision field
       and clear decision field.
    """
    # if item coming from config (recurring or itemtemplate), keep data as defined
    if original.isDefinedInTool():
        return

    newItem = event.newItem
    # copy decision from source items in destination's deliberation if item is accepted
    if original.query_state() in ['accepted', 'accepted_but_modified'] and newItem != original:
        newItem.setDecisionProject(original.getDecision())
    # clear decision for new item
    newItem.setDecision('<p>&nbsp;</p>')
    # when item send to another config, we must clean modification style
    if newItem.portal_type != original.portal_type:
        newItem.setDecisionProject(newItem.getDecisionProject().replace('class="mltcorrection"', ''))
    # Make sure we have 'text/html' for every Rich fields
    forceHTMLContentTypeForEmptyRichFields(newItem)
