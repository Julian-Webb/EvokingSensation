import unittest
from widgets import experimenter_window


class TestExperimenterWindow(unittest.TestCase):
    def test__validate_input(self):
        vi = experimenter_window._ParameterManager._validate_input

        self.assertTrue(
            vi(input_str='5', minimum='0', maximum='10', numeric_type="<class 'int'>")
        )
        self.assertTrue(
            vi(input_str='5', minimum='0', maximum='10', numeric_type="<class 'float'>")
        )
        self.assertFalse(
            vi(input_str='5.5', minimum='0', maximum='10', numeric_type="<class 'int'>")
        )
        self.assertTrue(
            vi(input_str='5.5', minimum='0', maximum='10', numeric_type="<class 'float'>")
        )
        self.assertFalse(
            vi(input_str='abc', minimum='0', maximum='10', numeric_type="<class 'int'>")
        )
        # out of range
        self.assertFalse(
            vi(input_str='15', minimum='5', maximum='10', numeric_type="<class 'int'>")
        )
        self.assertFalse(
            vi(input_str='1',  minimum='5', maximum='10', numeric_type="<class 'int'>")
        )

    def test_open_start_close(self):
        ex = experimenter_window.ExperimenterWindow()
        # open port > start > close port (stimulation should be stopped)
        ex.com_port_manager.open_port()
        ex.stimulation_buttons._on_start()
        ex.com_port_manager.close_port()


    # def test_open_start_stop(self):
    #     # open port > start > stop
    #     ex = experimenter_window.ExperimenterWindow()
    #     ex.com_port_manager.open_port()
    #     ex.stimulation_buttons._on_start()
    #     ex.stimulation_buttons._on_stop()

    # def test_open_start_stop_start(self):
    #     # open port > start > stop > start (stimulation should be restarted)
    #     ex = experimenter_window.ExperimenterWindow()
    #     ex.com_port_manager.open_port()
    #     ex.stimulation_buttons._on_start()
    #     ex.stimulation_buttons._on_stop()
    #     ex.stimulation_buttons._on_start()


