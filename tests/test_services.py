#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_opentranslink
----------------------------------

Tests for `opentranslink` module.
"""
# stdlib imports
import unittest

import os, sys
THIS_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.abspath(os.path.join(THIS_DIR, ".."))
if PARENT_DIR not in sys.path:
    sys.path = [ PARENT_DIR, ] + sys.path

# local imports
from opentranslink import InvalidServiceError
from opentranslink import Service


class TestServices(unittest.TestCase):

    def test_invalid_service_names(self):
        """Invalid service name throws exceptions
        """
        with self.assertRaises(InvalidServiceError):
            Service('metrov')

    def test_valid_service_names(self):
        """Valid service names don't throw exceptions
        """
        try:
            for service_name in ['metro', 'ulsterbus', 'goldline', 'nir', 'enterprise']:
                Service(service_name)
        except InvalidServiceError:
            self.fail('InvalidServiceError raised unexpectedly')

    def test_goldline_route_count(self):
        """Test that the goldline service returns the correct number of routes
        """
        service = Service('goldline')
        self.assertEqual(34, len(service.routes()))

    def test_metro_route_count(self):
        """Test that the metro service returns the correct number of routes
        """
        service = Service('metro')
        self.assertEqual(102, len(service.routes()))

    def test_ulsterbus_route_count(self):
        """Test that the ulsterbus service returns the correct number of routes
        """
        service = Service('ulsterbus')
        self.assertEqual(454, len(service.routes()))

    def test_nir_route_count(self):
        """Test that the nir service returns the correct number of routes
        """
        service = Service('nir')
        with self.assertRaises(NotImplementedError):
            service.routes()

    def test_enterprise_route_count(self):
        """Test that the enterprise service returns the correct number of routes
        """
        service = Service('enterprise')
        with self.assertRaises(NotImplementedError):
            service.routes()


if __name__ == '__main__':
    unittest.main()
