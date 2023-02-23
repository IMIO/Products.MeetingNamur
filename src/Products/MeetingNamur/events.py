# -*- coding: utf-8 -*-
#
# File: events.py
#
# Copyright (c) 2014 by Imio.be
#
# GNU General Public License (GPL)
#

__author__ = """Gauthier BASTIEN <gauthier.bastien@imio.be>"""
__docformat__ = 'plaintext'

from Products.PloneMeeting.utils import forceHTMLContentTypeForEmptyRichFields

def onItemLocalRolesUpdated(item, event):
    """Called after localRoles have been updated on the item."""
    item.adapted().updateMeetingCertifiedSignaturesWriterLocalRoles()

def onItemDuplicated(original, event):
    """After item's cloning, we copy in description field the decision field
       and clear decision field.
    """
    newItem = event.newItem
    # copy decision from source items in destination's deliberation if item is accepted
    if original.query_state() in ['accepted', 'accepted_but_modified'] and newItem != original:
        newItem.setDescription(original.getDecision())
    # clear decision for new item
    newItem.setDecision('<p>&nbsp;</p>')
    # when item send in other config, we must clean modification style
    if newItem.portal_plonemeeting.getMeetingConfig(newItem) != original.portal_plonemeeting.getMeetingConfig(original):
        newItem.setDescription(newItem.Description().replace('class="mltcorrection"', ''))
    # Make sure we have 'text/html' for every Rich fields
    forceHTMLContentTypeForEmptyRichFields(newItem)
