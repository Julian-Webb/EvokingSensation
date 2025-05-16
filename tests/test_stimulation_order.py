import unittest
from os import path
from backend.stimulation_order import StimulationOrder


class TestStimulationOrder(unittest.TestCase):
    def test_n_blocks_and_trials(self):
        stim_path = path.join('data', 'test_participant', 'stimulation_order.xlsx')
        so = StimulationOrder.from_file(str(stim_path))

        for _ in range(4):
            self.assertEqual(so.n_blocks(), 2, 'number of blocks should be 2')
            self.assertEqual(so.n_trials_in_current_block(), 2, 'number trials should be 2')
            so.next_trial()