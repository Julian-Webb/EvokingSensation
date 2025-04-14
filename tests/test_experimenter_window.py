import unittest
from settings import Settings
import experimenter_window


class TestExperimenterWindow(unittest.TestCase):
    def test__validate_input(self):
        vi = experimenter_window._ParameterManager._validate_input


        self.assertTrue(
            vi(input_str='5', input_range=(0, 10), numeric_type=int)
        )
        self.assertTrue(
            vi(input_str='5', input_range=(0, 10), numeric_type=float)
        )
        self.assertFalse(
            vi(input_str='5.5', input_range=(0, 10), numeric_type=int)
        )
        self.assertTrue(
            vi(input_str='5.5', input_range=(0, 10), numeric_type=float)
        )
        self.assertFalse(
            vi(input_str='abc', input_range=(0, 10), numeric_type=int)
        )
        # out of range
        self.assertFalse(
            vi(input_str='15', input_range=(5, 10), numeric_type=int)
        )
        self.assertFalse(
            vi(input_str='1', input_range=(5, 10), numeric_type=int)
        )
