import unittest
import tkinter as tk

from backend.locale_manager import LocaleManager
from widgets.evoked_sensations_frame import EvokedSensationsFrame, _SingleSensationFrame

LocaleManager().set_locale('German')


class TestEvokedSensationsFrame(unittest.TestCase):
    def test_check_complete_inputs(self):
        es_frame = EvokedSensationsFrame(tk.Frame(), lambda _: None, 1, 2)

        # continue button enabled when no sensations are entered
        self.assertEqual(str(es_frame.continue_button['state']), 'normal', 'continue button should be enabled initially')

        es_frame.add_sensation()
        self.assertEqual(str(es_frame.continue_button['state']), 'disabled',
                         "continue button should be disabled when there's an empty sensation")

        # partial entries
        es_frame.sensations_frames[0].type_var.set('Tingling')
        self.assertEqual(str(es_frame.continue_button['state']), 'disabled',
                         "continue button should stay disabled with only partial inputs")

        # full entries
        es_frame.sensations_frames[0].intensity_var.set(1)
        es_frame.sensations_frames[0].location_vars['D1'].set(True)

        self.assertEqual(str(es_frame.continue_button['state']), 'normal',
                         "continue button should be enabled with full inputs")

    def test_all_inputs_filled(self):
        self.callback_works = False

        def callback(*_):
            self.callback_works = True

        single_sense = _SingleSensationFrame(tk.Frame(), 1, lambda *_: None, on_input_callback=callback)

        # No entries
        self.assertFalse(single_sense.all_inputs_filled())

        # partial entries
        single_sense.intensity_var.set(1)
        self.assertTrue(self.callback_works)
        self.assertFalse(single_sense.all_inputs_filled())

        # full entries
        single_sense.type_var.set('Tingling')
        single_sense.location_vars['D1'].set(True)
        self.assertTrue(single_sense.all_inputs_filled())
