Products.MeetingNamur Changelog
===============================

Older versions than 3.0 can be found at http://svn.communesplone.org/svn/communesplone/MeetingNamur/tags/
The Products.MeetingNamur version must be the same as the Products.PloneMeeting version

4.2.0a3 (2023-04-06)
--------------------

- New proper release.
  [aduchene]


4.2.0a2 (2023-04-06)
--------------------

- Adapted code regarding removal of MeetingConfig.useGroupsAsCategories. 
  [gbastien]

4.2.0a1 (2023-02-23)
--------------------

- Compatible for PloneMeeting 4.2.
  [aduchene]
- Fixed broken tests.
  [aduchene]

4.1.3 (2021-08-05)
------------------

- Changed translations.
  [aduchene]

4.1.2 (2021-04-28)
------------------

- Added additional_catalog_query parameter in `getPrintableItemsByCategory`.
  [aduchene]

4.1.1 (2021-02-15)
------------------

- Fixed failing tests for which name changed in `Products.PloneMeeting`.
  [gbastien]
- Fixed a bug in `getPrintableItemsByCategory` where first level category was not taken into account.
  [aduchene]

4.1 (2020-10-20)
----------------
- Using MeetingCommunes
- Compatible for PloneMeeting 4.1.26
- Adapted code and tests regarding DX meetingcategory
- Adapted templates regarding last changes in Products.PloneMeeting

4.0 (2017)
----------
- Adapted workflows to define the icon to use for transitions
- Removed field MeetingConfig.cdldProposingGroup and use the 'indexAdvisers' value
  defined in the 'searchitemswithfinanceadvice' collection to determinate what are
  the finance adviser group ids
- 'getEchevinsForProposingGroup' does also return inactive MeetingGroups so when used
  as a TAL condition in a customAdviser, an inactive MeetingGroup/customAdviser does
  still behaves correctly when updating advices
- Use ToolPloneMeeting.performCustomWFAdaptations to manage our own WFAdaptation
  (override of the 'no_publication' WFAdaptation)
- Adapted tests, keep test... original PM files to overrides original PM tests and
  use testCustom... for every other tests, added a testCustomWorkflow.py
- Now that the same WF may be used in several MeetingConfig in PloneMeeting, removed the
  2 WFs meetingcollege and meetingcouncil and use only one meetingcommunes where wfAdaptations
  'no_publication' and 'no_global_observation' are enabled
- Added profile 'financesadvice' to manage advanced finances advice using a particular
  workflow and a specific meetingadvicefinances portal_type

3.3 (2015-07-10)
----------------
- Updated regarding changes in PloneMeeting
- Removed profile 'examples' that loaded examples in english
- Removed dependencies already defined in PloneMeeting's setup.py
- Added parameter MeetingConfig.initItemDecisionIfEmptyOnDecide that let enable/disable
- items decision field initialization when meeting 'decide' transition is triggered
- Added MeetingConfig 'CoDir'
- Added MeetingConfig 'CA'
- Field 'MeetingGroup.signatures' was moved to PloneMeeting

3.2.0.1 (2014-03-06)
--------------------
- Updated regarding changes in PloneMeeting
- Moved some translations from the plone domain to the PloneMeeting domain

3.2.0 (2014-02-12)
------------------
- Updated regarding changes in PloneMeeting
- Use getToolByName where necessary

3.1.0 (2014-07-15)
- Simplified overrides now that PloneMeeting manage this correctly

3.0.3 (unreleased)
------------------
- Nothing yet

3.0.2 (2013-06-21)
------------------
- Removed override of Meeting.mayChangeItemsOrder
- Removed override of meeting_changeitemsorder
- Removed override of browser.async.Discuss.isAsynchToggleEnabled, now enabled by default
- Added missing tests from PloneMeeting
- Corrected bug in printAdvicesInfos leading to UnicodeDecodeError when no advice was asked on an item

3.0.1 (2013-06-07)
------------------
- Added sample of document template with printed annexes
- Added method to ease pritning of assembly with 'category' of assembly members
- Make printing by category as functionnal as printing without category
- Corrected bug while going back to published that could raise a WorkflowException sometimes

3.0 (2013-04-03)
----------------
- Migrated to Plone 4 (use PloneMeeting 3.x, see PloneMeeting's HISTORY.txt for full changes list)

2.1.3 (2012-09-19)
------------------
- Added possibility to give, modify and view an advice on created item
- Added possibility to define a decision of replacement when an item is delayed
- Added new workflow adaptation to add publish state with hidden decision for no meeting-manager
