# -*- coding: utf-8 -*-
from plone.testing import z2, zca
from plone.app.testing import FunctionalTesting
from plone.app.testing import PloneWithPackageLayer
import Products.MeetingNamur


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
