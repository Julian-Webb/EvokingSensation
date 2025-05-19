import os
from collections import OrderedDict
import tkinter as tk
from backend.stimulator import StimulationParameters


# We ignore unresolved references because we initialize properties with setattr, and it doesn't understand this.
# noinspection PyUnresolvedReferences
class Settings:
    """singleton Settings for the stimulation application.

    Attributes:
        participant_folder_var: The tk.StringVar which stores the base directory for the participant data.
        amplitude: The tk.DoubleVar for amplitude in milli ampere.
        frequency: The tk.DoubleVar for frequency in Hz.
        phase_duration: The tk.IntVar for phase duration in microseconds.
        interphase_interval: The tk.IntVar for time between the positive and negative phase of a pulse in microseconds.
        stim_duration: The tk.DoubleVar for stimulation duration in seconds.
        channel: The tk.IntVar for channel number (1-8). refer to labels on the device.
    """
    _instance = None

    # Countdown duration before stimulation
    COUNTDOWN_DURATION = 1  # todo change to 3

    PARAMETER_OPTIONS = OrderedDict(
        {
            'channel': {'label': 'Channel (testing only)', 'unit': '',
                        'range': (1, 8), 'increment': 1, 'numeric_type': int, 'default': 1},
            'amplitude': {'label': 'Amplitude', 'unit': 'mA',
                          'range': (0.5, 11), 'increment': 0.5, 'numeric_type': float, 'default': 2.0},
            'phase_duration': {'label': 'Phase duration', 'unit': 'µs',
                               'range': (1, 1000), 'increment': 50, 'numeric_type': int, 'default': 700},
            'interphase_interval': {'label': 'Interphase interval', 'unit': 'µs',
                                    'range': (1, 1000), 'increment': 50, 'numeric_type': int, 'default': 500},
            'stim_duration': {'label': 'Stimulation Duration', 'unit': 's',
                              'range': (0.1, 240), 'increment': 1, 'numeric_type': float,
                              # 'default': 5
                              'default': 0.1  # todo change back
                              },
            'frequency': {'label': 'Frequency', 'unit': 'Hz',
                          'range': (1, 1000), 'increment': 1.0, 'numeric_type': float, 'default': 50.0},
        }
    )

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Settings, cls).__new__(cls, *args, **kwargs)
            ci = cls._instance  # alias for readability

            # Variable for the path
            # todo handling for actual path
            base_path = 'C:\\Users\\julia\\PycharmProjects\\EvokingSensation'
            # ci.participant_data_dir = tk.StringVar(value=os.path.join(base_path, 'data', 'test_participant'))
            ci.participant_folder_var = tk.StringVar(value=os.path.join(base_path, 'data', 'test_participant'))

            # Initialize tk.IntVars / tk.DoubleVars for all parameters corresponding to their type
            for property_name, options in cls.PARAMETER_OPTIONS.items():
                numeric_class = tk.DoubleVar if options['numeric_type'] is float else tk.IntVar
                var = numeric_class(value=options['default'])
                setattr(ci, property_name, var)

            # Link a period variable to the frequency
            ci.period_string_var = tk.StringVar()
            ci._update_period_from_frequency()
            ci.frequency.trace_add('write', ci._update_period_from_frequency)

        return cls._instance

    def get_stimulation_parameters(self) -> StimulationParameters:
        """
        :return: StimulationParameters object with the current configuration of amplitude, phase duration, interphase interval, and period.
        """
        return StimulationParameters(self.amplitude.get(), self.phase_duration.get(), self.interphase_interval.get(),
                                     self.period_numeric())

    def _update_period_from_frequency(self, *_) -> None:
        """Update the period based on the frequency."""
        try:
            self.period_string_var.set(f"{self.period_numeric():.2f}")
        except (ValueError, ZeroDivisionError, tk.TclError):
            self.period_string_var.set('Invalid Frequency Value')

    def period_numeric(self) -> float:
        return (1 / self.frequency.get()) * 1000  # Convert to milliseconds

    def get_stim_order_path(self) -> str:
        """The path for the stimulation order file."""
        return os.path.join(self.participant_folder_var.get(), 'stimulation_order.xlsx')

    def get_sensation_data_path(self) -> str:
        """The path for the file storing the sensation data the participant entered."""
        return os.path.join(self.participant_folder_var.get(), 'sensation_data.json')

    def get_calibration_data_path(self) -> str:
        """The path for the file storing what happened during calibration"""
        return os.path.join(self.participant_folder_var.get(), 'calibration_data.json')
