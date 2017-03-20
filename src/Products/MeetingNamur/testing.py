# -*- coding: utf-8 -*-
from plone.testing import z2, zca
from plone.app.testing import PloneWithPackageLayer
from plone.app.testing import FunctionalTesting
import Products.MeetingNamur
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE


MNA_ZCML = zca.ZCMLSandbox(filename="testing.zcml",
                           package=Products.MeetingNamur,
                           name='MNA_ZCML')

MNA_Z2 = z2.IntegrationTesting(bases=(z2.STARTUP, MNA_ZCML),
                               name='MNA_Z2')

MNA_TESTING_PROFILE = PloneWithPackageLayer(
    zcml_filename="testing.zcml",
    zcml_package=Products.MeetingNamur,
    additional_z2_products=('imio.dashboard',
                            'Products.MeetingNamur',
                            'Products.PloneMeeting',
                            'Products.CMFPlacefulWorkflow',
                            'Products.PasswordStrength'),
    gs_profile_id='Products.MeetingNamur:testing',
    name="MNA_TESTING_PROFILE")

MNA_TESTING_PROFILE_FUNCTIONAL = FunctionalTesting(
    bases=(MNA_TESTING_PROFILE,), name="MNA_TESTING_PROFILE_FUNCTIONAL")

MNA_TESTING_ROBOT = FunctionalTesting(
    bases=(
        MNA_TESTING_PROFILE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name="MNA_TESTING_ROBOT",
)
