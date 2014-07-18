from Products.Archetypes.atapi import MultiSelectionWidget
from Products.Archetypes.atapi import LinesField
from Products.Archetypes.atapi import TextField
from Products.Archetypes.atapi import TextAreaWidget
from Products.Archetypes.atapi import StringField
from Products.Archetypes.atapi import Schema
from Products.PloneMeeting.Meeting import Meeting
from Products.PloneMeeting.MeetingItem import MeetingItem
from Products.PloneMeeting.MeetingGroup import MeetingGroup
from Products.PloneMeeting.MeetingConfig import MeetingConfig


def update_group_schema(baseSchema):

    specificSchema = Schema((

        # field used to define list of services for echevin for a MeetingGroup
        LinesField(
            name='echevinServices',
            widget=MultiSelectionWidget(
                size=10,
                label='EchevinServices',
                label_msgid='MeetingCommune_label_echevinServices',
                description='Leave empty if he is not an echevin',
                description_msgid='MeetingCommune_descr_echevinServices',
                i18n_domain='PloneMeeting',
            ),
            enforceVocabulary=True,
            multiValued=1,
            vocabulary='listEchevinServices',
        ),

        # field used to define specific signatures for a MeetingGroup
        TextField(
            name='signatures',
            widget=TextAreaWidget(
                label='Signatures',
                label_msgid='MeetingCommune_label_signatures',
                description='Leave empty to use the signatures defined on the meeting',
                description_msgid='MeetingCommune_descr_signatures',
                i18n_domain='PloneMeeting',
            ),
        ),
    ),)

    completeSchema = baseSchema + specificSchema.copy()
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
    ),)

    baseSchema['description'].write_permission = "MeetingNamur: Write description"
    baseSchema['description'].widget.label = "projectOfDecision"
    baseSchema['description'].widget.label_msgid = "projectOfDecision_label"

    completeSchema = baseSchema + specificSchema.copy()
    return completeSchema
MeetingItem.schema = update_item_schema(MeetingItem.schema)


def update_meeting_schema(baseSchema):

    specificSchema = Schema((
    ),)

    baseSchema['assembly'].widget.description_msgid = "assembly_meeting_descr"

    completeSchema = baseSchema + specificSchema.copy()
    return completeSchema
Meeting.schema = update_meeting_schema(Meeting.schema)


def update_config_schema(baseSchema):
    specificSchema = Schema((

        TextField(
            name='itemDecisionReportText',
            widget=TextAreaWidget(
                description="ItemDecisionReportText",
                description_msgid="item_decision_report_text_descr",
                label='ItemDecisionReportText',
                label_msgid='PloneMeeting_label_itemDecisionReportText',
                i18n_domain='PloneMeeting',
            ),
            allowable_content_types=('text/plain', 'text/html', ),
            default_output_type="text/plain",
        ),

        TextField(
            name='itemDecisionRefuseText',
            widget=TextAreaWidget(
                description="ItemDecisionRefuseText",
                description_msgid="item_decision_refuse_text_descr",
                label='ItemDecisionRefuseText',
                label_msgid='PloneMeeting_label_itemDecisionRefuseText',
                i18n_domain='PloneMeeting',
            ),
            allowable_content_types=('text/plain', 'text/html', ),
            default_output_type="text/plain",
        )
    ),)

    completeConfigSchema = baseSchema + specificSchema.copy()
    completeConfigSchema.moveField('itemDecisionReportText', after='budgetDefault')
    completeConfigSchema.moveField('itemDecisionRefuseText', after='itemDecisionReportText')
    return completeConfigSchema
MeetingConfig.schema = update_config_schema(MeetingConfig.schema)

# Classes have already been registered, but we register them again here
# because we have potentially applied some schema adaptations (see above).
# Class registering includes generation of accessors and mutators, for
# example, so this is why we need to do it again now.
from Products.PloneMeeting.config import registerClasses
registerClasses()
