from collections import OrderedDict
import tkinter as tk


class Settings:
    """Singleton Settings for the stimulation application.

    Attributes:
        amplitude (float): The tk.DoubleVar for amplitude in milli ampere.
        frequency (float): The tk.DoubleVar for frequency in Hz.
        phase_duration (int): The tk.IntVar for phase duration in microseconds.
        interphase_interval (int): The tk.IntVar for time between the positive and negative phase of a pulse in microseconds.
        stim_duration (float): The tk.DoubleVar for stimulation duration in seconds.
        channel (int): The tk.IntVar for channel number (1-8). Refer to labels on the device.
    """
    _instance = None

    PARAMETER_OPTIONS = OrderedDict(
        {
            'channel': {'label': 'Channel (testing only)', 'range': (1, 8), 'increment': 1, 'numeric_type': int,
                        'default': 1},
            'amplitude': {'label': 'Amplitude (mA)', 'range': (0.5, 11), 'increment': 0.5, 'numeric_type': float,
                          'default': 2.0},
            'phase_duration': {'label': 'Phase duration (µs)', 'range': (1, 1000), 'increment': 50, 'numeric_type': int,
                               'default': 700},
            'interphase_interval': {'label': 'Interphase interval (µs)', 'range': (1, 1000), 'increment': 50,
                                    'numeric_type': int, 'default': 500},
            'stim_duration': {'label': 'Stimulation Duration (s)', 'range': (0.1, 240), 'increment': 1,
                              'numeric_type': float,
                              # 'default': 5
                              'default': 0.1 # todo change back
                              },
            'frequency': {'label': 'Frequency (Hz)', 'range': (1, 1000), 'increment': 1.0, 'numeric_type': float,
                          'default': 50.0},
        }
    )

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Settings, cls).__new__(cls, *args, **kwargs)

            # aliases for readability
            ci = cls._instance
            po = cls.PARAMETER_OPTIONS

            # Initialize Vars for each parameter with default values
            # It's essential to keep a reference to the tk.StringVars to avoid garbage collection!
            ci.amplitude = tk.DoubleVar(value=po['amplitude']['default'])
            ci.phase_duration = tk.IntVar(value=po['phase_duration']['default'])
            ci.interphase_interval = tk.IntVar(value=po['interphase_interval']['default'])
            ci.stim_duration = tk.DoubleVar(value=po['stim_duration']['default'])
            ci.channel = tk.IntVar(value=po['channel']['default'])

            # Create linked DoubleVars for period and frequency
            ci.frequency = tk.DoubleVar(value=po['frequency']['default'])
            ci.period_string_var = tk.StringVar()
            ci._update_period_from_frequency()
            ci.frequency.trace_add('write', ci._update_period_from_frequency)

        return cls._instance

    def _update_period_from_frequency(self, *_):
        """Update the period based on the frequency."""
        try:
            self.period_string_var.set(f"{self.period_numeric():.2f}")
        except (ValueError, ZeroDivisionError, tk.TclError):
            self.period_string_var.set('Invalid Frequency Value')

    def period_numeric(self):
        return (1 / self.frequency.get()) * 1000  # Convert to milliseconds

