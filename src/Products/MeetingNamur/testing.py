# -*- coding: utf-8 -*-
from plone.testing import z2, zca
from plone.app.testing import PloneWithPackageLayer
from plone.app.testing import FunctionalTesting
import Products.MeetingNamur


MNA_ZCML = zca.ZCMLSandbox(filename="testing.zcml",
                           package=Products.MeetingNamur,
                           name='MNA_ZCML')

MNA_Z2 = z2.IntegrationTesting(bases=(z2.STARTUP, MNA_ZCML),
                               name='MNA_Z2')

MNA_TEST_PROFILE = PloneWithPackageLayer(
    zcml_filename="testing.zcml",
    zcml_package=Products.MeetingNamur,
    additional_z2_products=('Products.MeetingNamur',
                            'Products.PloneMeeting',
                            'Products.CMFPlacefulWorkflow'),
    gs_profile_id='Products.MeetingNamur:testing',
    name="MNA_TEST_PROFILE")

MNA_TEST_PROFILE_FUNCTIONAL = FunctionalTesting(
    bases=(MNA_TEST_PROFILE,), name="MNA_TEST_PROFILE_FUNCTIONAL")
