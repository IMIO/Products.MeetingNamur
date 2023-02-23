# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 by Imio.be
#
# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#

from AccessControl import Unauthorized
from plone import api
from plone.z3cform.layout import wrap_form
from Products.CMFCore.utils import getToolByName
from Products.PloneMeeting.config import PMMessageFactory as _
from Products.PloneMeeting.interfaces import IRedirect
from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form.contentprovider import ContentProviders
from z3c.form.interfaces import IFieldsAndContentProvidersForm
from zope import interface
from zope import schema
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from zope.component.hooks import getSite
from zope.contentprovider.provider import ContentProviderBase
from zope.i18n import translate
from zope.interface import implements


def item_certified_signatures_default():
    """
      Returns the itemSignatures of the item.
      As from zope.schema._bootstrapinterfaces import IContextAwareDefaultFactory
      does not seem to work, we have to get current context manually...
    """
    context = getSite().REQUEST['PUBLISHED'].context
    itemCertifiedSignatures = context.getRawItemCertifiedSignatures(content_type='text/plain')
    if not isinstance(itemCertifiedSignatures, unicode):
        itemCertifiedSignatures = unicode(itemCertifiedSignatures, 'utf-8')
    return itemCertifiedSignatures


class IManageItemCertifiedSignatures(interface.Interface):
    item_certified_signatures = schema.Text(title=_(u"Item certified signatures to apply"),
                                            description=_(u"Enter the item certified signatures to be applied."),
                                            defaultFactory=item_certified_signatures_default,
                                            required=False,)


class DisplayCertifiedSignaturesProvider(ContentProviderBase):
    """
      This ContentProvider will just display the signatures defined on the linked meeting.
    """
    template = ViewPageTemplateFile('templates/display_certified_signatures.pt')

    def __init__(self, context, request, view):
        super(DisplayCertifiedSignaturesProvider, self).__init__(context, request, view)
        self.__parent__ = view

    def getItemCertifiedSignatures(self):
        return self.context.getItemCertifiedSignatures().replace('\n', '<br />')

    def render(self):
        return self.template()


class ManageItemCertifiedSignaturesForm(form.Form):
    """
      This form will help to manage itemCertifiedSignatures by being able to redefine it on a single
      item without having to use the edit form.
    """
    implements(IFieldsAndContentProvidersForm)

    fields = field.Fields(IManageItemCertifiedSignatures)
    ignoreContext = True  # don't use context to get widget data

    contentProviders = ContentProviders()
    contentProviders['itemCertifiedSignatures'] = DisplayCertifiedSignaturesProvider
    # put the 'itemCertifiedSignatures' in first position
    contentProviders['itemCertifiedSignatures'].position = 0
    contentProviders['itemCertifiedSignatures'].size = 8
    label = _(u"Manage item certified signatures")
    description = u''
    _finishedSent = False

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.label = translate('Manage item certified signatures',
                               domain='PloneMeeting',
                               context=self.request)

    @button.buttonAndHandler(_('Apply'), name='apply_item_certified_signatures')
    def handleApplyItemCertifiedSignatures(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        # do adapt item signatures
        self.item_certified_signatures = self.request.form.get('form.widgets.item_certified_signatures')
        self._doApplyItemCertifiedSignatures()

    @button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self, action):
        self._finishedSent = True

    def update(self):
        """ """
        # raise Unauthorized if current user can not manage itemAssembly
        if not api.user.get_current().has_permission('MeetingNamur: Write certified signatures',
                                                                         self.context):
            raise Unauthorized

        super(ManageItemCertifiedSignaturesForm, self).update()
        # after calling parent's update, self.actions are available
        self.actions.get('cancel').addClass('standalone')

    def updateWidgets(self):
        # XXX manipulate self.fields BEFORE doing form.Form.updateWidgets
        form.Form.updateWidgets(self)

    def render(self):
        if self._finishedSent:
            IRedirect(self.request).redirect(self.context.absolute_url())
            return ""
        return super(ManageItemCertifiedSignaturesForm, self).render()

    def _doApplyItemCertifiedSignatures(self):
        """
          The method actually do the job, set the itemSignatures on self.context
          and following items if defined
        """
        user = self.context.portal_membership.getAuthenticatedMember()
        if not user.has_permission('MeetingNamur: Write certified signatures',
                                                                         self.context):

            raise Unauthorized

        self.context.setItemCertifiedSignatures(self.item_certified_signatures)

        plone_utils = getToolByName(self.context, 'plone_utils')
        plone_utils.addPortalMessage(_("Item certified signatures have been updated."))
        self._finishedSent = True


ManageItemCertifiedSignaturesFormWrapper = wrap_form(ManageItemCertifiedSignaturesForm)
