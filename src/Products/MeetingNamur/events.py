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


def onItemDuplicated(original, event):
    '''After item's cloning, we copy in description field the decision field
       and clear decision field.
    '''
    newItem = event.newItem
    #copy decision from source items in destination's deliberation if item is accepted
    if original.queryState() in ['accepted', 'accepted_but_modified'] and newItem != original:
        newItem.setDescription(original.getDecision())
    #clear decision for new item
    newItem.setDecision('<p>&nbsp;</p>')
