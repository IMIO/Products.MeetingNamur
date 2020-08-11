from Products.Archetypes.atapi import BooleanField
from Products.Archetypes.atapi import LinesField
from Products.Archetypes.atapi import MultiSelectionWidget
from Products.Archetypes.atapi import RichWidget
from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import StringField
from Products.Archetypes.atapi import TextAreaWidget
from Products.Archetypes.atapi import TextField
from Products.PloneMeeting.config import registerClasses
from Products.PloneMeeting.Meeting import Meeting
from Products.PloneMeeting.MeetingGroup import MeetingGroup
from Products.PloneMeeting.MeetingItem import MeetingItem


def update_group_schema(baseSchema):
    completeSchema = baseSchema
    completeSchema['acronym'].widget.description = "Acronym"
    completeSchema['acronym'].widget.description_msgid = "meetingNamur_acronym_descri_msgid"
    return completeSchema


MeetingGroup.schema = update_group_schema(MeetingGroup.schema)


def update_item_schema(baseSchema):
    specificSchema = Schema((

        StringField(
            name='grpBudgetInfos',
            widget=MultiSelectionWidget(
                description="GrpBudgetInfos",
                description_msgid="MeetingNamur_descr_grpBudgetInfos",
                size=10,
                label='GrpBudgetInfos',
                label_msgid='MeetingNamur_label_grpBudgetInfos',
                i18n_domain='PloneMeeting',
            ),
            vocabulary='listGrpBudgetInfosAdviser',
            multiValued=1,
            enforceVocabulary=False,
        ),

        # field used to define specific certified signatures for a MeetingItem
        TextField(
            name='itemCertifiedSignatures',
            widget=TextAreaWidget(
                label='Signatures',
                label_msgid='PloneMeeting_label_certifiedSignatures',
                description='Leave empty to use the certified signatures defined on the meeting or MeetingGroup',
                description_msgid='MeetingNamur_descr_certified_signatures',
                i18n_domain='PloneMeeting',
            ),
            write_permission='MeetingNamur: Write certified signatures',
            allowable_content_types=('text/plain',),
            default_output_type='text/plain',
            default_content_type='text/plain',
        ),

        # field use to specify if this item is privacy (in this case, it's not visible in public pv)
        BooleanField(
            name='isConfidentialItem',
            default=False,
            widget=BooleanField._properties['widget'](
                condition="python: here.portal_plonemeeting.isManager(here)",
                label='IsConfidentialItem',
                label_msgid='MeetingNamur_isConfidentialItem',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
        ),
        TextField(
            name='vote',
            widget=RichWidget(
                condition="python: here.attributeIsUsed('vote')",
                description="Vote",
                description_msgid="item_vote_descr",
                label='Vote',
                label_msgid='MeetingNamur_vote',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
            write_permission="PloneMeeting: Write item MeetingManager reserved fields",
            default_content_type="text/html",
            allowable_content_types=('text/html',),
            default_output_type="text/x-html-safe",
        ),
    ), )

    baseSchema['description'].write_permission = "MeetingNamur: Write description"
    baseSchema['description'].widget.label = "projectOfDecision"
    baseSchema['description'].widget.label_msgid = "projectOfDecision_label"

    completeSchema = baseSchema + specificSchema.copy()
    return completeSchema


MeetingItem.schema = update_item_schema(MeetingItem.schema)


def update_meeting_schema(baseSchema):
    specificSchema = Schema((
    ), )

    baseSchema['assembly'].widget.description_msgid = "assembly_meeting_descr"

    completeSchema = baseSchema + specificSchema.copy()
    return completeSchema


Meeting.schema = update_meeting_schema(Meeting.schema)

# Classes have already been registered, but we register them again here
# because we have potentially applied some schema adaptations (see above).
# Class registering includes generation of accessors and mutators, for
# example, so this is why we need to do it again now.

registerClasses()
