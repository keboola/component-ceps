"""
Created on 12. 11. 2018

@author: esner
"""

import os
import unittest
from unittest import mock

from freezegun import freeze_time
from keboola.component.exceptions import UserException

from component import Component


class TestComponent(unittest.TestCase):
    # set global time to 2010-10-10 - affects functions like datetime.now()
    @freeze_time("2010-10-10")
    # set KBC_DATADIR env to non-existing dir
    @mock.patch.dict(os.environ, {"KBC_DATADIR": "./non-existing-dir"})
    def test_run_no_cfg_fails(self):
        with self.assertRaises(ValueError):
            comp = Component()
            comp.run()

    def test_validate_granularities_supported_passes(self):
        endpoints = [
            {"endpoint_name": "Load", "granularity": "YR"},
            {"endpoint_name": "Frekvence", "granularity": "HR"},
            {"endpoint_name": "RegulationEnergy", "granularity": "None"},
        ]
        Component.validate_granularities(endpoints, continue_on_fail=False)

    def test_validate_granularities_unsupported_fails_without_continue_on_fail(self):
        endpoints = [{"endpoint_name": "AktivaceSVRvCR", "granularity": "MO"}]
        with self.assertRaisesRegex(UserException, 'AktivaceSVRvCR does not support granularity "MO"'):
            Component.validate_granularities(endpoints, continue_on_fail=False)

    def test_validate_granularities_unsupported_warns_with_continue_on_fail(self):
        endpoints = [
            {"endpoint_name": "Generation", "granularity": "MI"},
            {"endpoint_name": "Load", "granularity": "None"},
            {"endpoint_name": "Load", "granularity": "HR"},
        ]
        with self.assertLogs(level="WARNING") as logs:
            valid = Component.validate_granularities(endpoints, continue_on_fail=True)
        self.assertIn('Generation does not support granularity "MI"', logs.output[0])
        self.assertIn('Load does not support granularity "None"', logs.output[0])
        self.assertIn("These endpoints are skipped.", logs.output[0])
        self.assertEqual(valid, [{"endpoint_name": "Load", "granularity": "HR"}])

    def test_validate_granularities_emergency_exchange_period_granularities_unsupported(self):
        for granularity in ["WE", "MO", "YR"]:
            endpoints = [{"endpoint_name": "EmergencyExchange", "granularity": granularity}]
            with self.assertRaisesRegex(UserException, "Supported: QH, HR, DY."):
                Component.validate_granularities(endpoints, continue_on_fail=False)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
