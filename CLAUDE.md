# Products.MeetingNamur

Plone product customizing the decision-making process (deliberations) for the **City of Namur**. Part of the PloneMeeting ecosystem managed by iMio.

## Architecture

Three-tier inheritance:

```
Products.PloneMeeting        (base framework)
  └─ Products.MeetingCommunes (Belgian communes profile)
       └─ Products.MeetingNamur (Namur-specific)
```

All three live under `../` as sibling `src/` packages in the same buildout.

**Stack:** Python 2.7, Plone 4.3, Zope 2.

## Package layout

Source is in `src/Products/MeetingNamur/`:

| Path | Purpose |
|---|---|
| `config.py` | Constants, custom permission (`WriteDecisionProject`), budget reviewer groups, item validation workflow levels |
| `interfaces.py` | Zope interfaces for workflow actions/conditions (College + Council variants), browser layer `IMeetingNamurLayer` |
| `adapters.py` | Main customization file (~900 lines). Custom adapters for MeetingConfig, Meeting, MeetingItem, ToolPloneMeeting. Workflow action/condition classes |
| `events.py` | Event handlers: `onItemLocalRolesUpdated` (budget reviewer roles), `onItemDuplicated` (copies decision to decisionProject) |
| `setuphandlers.py` | GenericSetup import step handlers |
| `model/pm_updates.py` | Archetypes schema extensions: custom fields (grpBudgetInfos, itemCertifiedSignatures, isConfidentialItem, vote, decisionProject, justification) |
| `browser/` | Z3C form for certified signatures management, view overrides |
| `skins/` | CMFSkins layers: CSS, images, page templates (meetingitem_view.pt, meetingitem_edit.pt) |
| `profiles/default/` | GenericSetup profile (workflows, skins, CSS/JS registries, permissions) |
| `profiles/testing/` | Test profile |
| `profiles/examples_fr/` | French demo data |
| `migrations/` | Upgrade steps (4.1, 4.2, 4.2.1) |
| `locales/` | i18n translations (fr, en, nl, de, es). Domain: `MeetingNamur` |

## Key concepts

- **Meeting configs**: `meeting-config-college` (College) and `meeting-config-council` (Council). Each has its own workflow variant.
- **Item validation chain**: itemcreated -> proposed_to_servicehead -> proposed_to_officemanager -> proposed_to_divisionhead -> proposed. Each level maps to a group suffix (creators, serviceheads, officemanagers, divisionheads, reviewers).
- **Workflow adaptations**: Defined in `adapters.py::customWfAdaptations`. Include shortcuts, extra decided states (accepted_but_modified, postpone_next_meeting, refused, delayed, etc.).
- **Budget impact reviewers**: Extra group suffix `budgetimpactreviewers` configured in `config.py`. Applied to specific financial departments.
- **Adapter pattern**: Customization is done by registering named adapters for `IMeetingConfigCustom`, `IMeetingCustom`, `IMeetingItemCustom`, `IToolPloneMeetingCustom`. Workflow actions/conditions are also adapter-based (College and Council variants registered in `configure.zcml`).

## Development

### Buildout

From the buildout root:

```bash
make buildout          # Run buildout
make run               # Start ZEO + instance1 (foreground) + LibreOffice
make libreoffice       # Start LibreOffice Docker container on port 2002
make stop-libreoffice  # Stop LibreOffice container
```

The package-level `buildout.cfg` extends `communes-dev.cfg` from the IMIO/buildout.pm repo and develops this package in-place.

### Running tests

LibreOffice must be running (port 2002) for document generation tests.

```bash
# From buildout root:
make test                        # Run all MeetingCommunes tests (default test_suite)
make test args=testMeetingItem   # Run a specific test file

# Or directly with the test runner:
bin/testnamur                          # All MeetingNamur tests
bin/testnamur -t testWorkflows         # Specific test module
bin/testnamur -t test_method_name      # Specific test method
```

### Test structure

- Base class: `MeetingNamurTestCase` (extends `MeetingCommunesTestCase`) in `tests/MeetingNamurTestCase.py`
- Test helpers: `tests/helpers.py`
- Test layer: `MNA_TESTING_PROFILE_FUNCTIONAL` (defined in `testing.py`)
- Ignored parent tests: `testPerformances.py`, `testVotes.py`, `test_robot.py`
- Tests inherit from both MeetingCommunes and the local test case, reusing the parent test suite with Namur-specific setup

## Version

Current: **4.2.4.dev0** (GPL). Changelog in `CHANGES.rst`.
