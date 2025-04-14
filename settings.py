import logging
from collections import OrderedDict
import tkinter as tk


class Settings:
    """Singleton Settings for the stimulation application.

    Attributes:
        amplitude (float): The tk.StringVar for amplitude in milli ampere.
        frequency (float): The tk.StringVar for frequency in Hz.
        pulse_width (int): The tk.StringVar for pulse width in microseconds.
        inter_pulse_width (int): The tk.StringVar for time between the positive and negative phase of a pulse in microseconds.
        stim_duration (float): The tk.StringVar for stimulation duration in seconds.
        channel (int): The tk.StringVar for channel number (1-8). Refer to labels on device.
    """
    _instance = None

    # IMPORTANT: Make values for period match values for frequency and vice versa
    PARAMETER_OPTIONS = OrderedDict(
        {
            'channel': {'label': 'Channel', 'range': (1, 8), 'increment': 1, 'numeric_type': int, 'default': 1},
            'amplitude': {'label': 'Amplitude (mA)', 'range': (0.5, 20), 'increment': 0.5, 'numeric_type': float,
                          'default': 2.0},
            'pulse_width': {'label': 'Pulse Width (µs)', 'range': (1, 1000), 'increment': 10, 'numeric_type': int,
                            'default': 100},
            'inter_pulse_width': {'label': 'Inter-Pulse Width (µs)', 'range': (1, 1000), 'increment': 10,
                                  'numeric_type': int, 'default': 200},
            'stim_duration': {'label': 'Stimulation Duration (s)', 'range': (1, 240), 'increment': 1,
                              'numeric_type': float, 'default': 10},
            'frequency': {'label': 'Frequency (Hz)', 'range': (1, 100), 'increment': 1, 'numeric_type': float,
                          'default': 10.0},
        }
    )

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Settings, cls).__new__(cls, *args, **kwargs)

            # aliases for readability
            ci = cls._instance
            po = cls.PARAMETER_OPTIONS

            # Initialize StringVars for each parameter with default values
            # It's essential to keep a reference to the tk.StringVars to avoid garbage collection!
            ci.amplitude = tk.StringVar(value=str(po['amplitude']['default']))
            ci.pulse_width = tk.StringVar(value=str(po['pulse_width']['default']))
            ci.inter_pulse_width = tk.StringVar(value=str(po['inter_pulse_width']['default']))
            ci.stim_duration = tk.StringVar(value=str(po['stim_duration']['default']))
            ci.channel = tk.StringVar(value=str(po['channel']['default']))

            # Create linked StringVars for period and frequency
            ci.frequency = tk.StringVar(value=str(po['frequency']['default']))
            ci.period = tk.StringVar()
            ci._update_period_from_frequency()
            ci.frequency.trace_add('write', ci._update_period_from_frequency)

        return cls._instance

    def _update_period_from_frequency(self, *_):
        """Update the period based on the frequency."""
        logging.debug('In _update_period_from_frequency')
        try:
            frequency = float(self.frequency.get())
            period = (1 / frequency) * 1000  # Convert to milliseconds
            self.period.set(f"{period:.2f}")
        except ValueError:
            logging.error('Invalid frequency value')
            raise ValueError

    @property
    def channel_adjusted(self):
        """Adjusted channel number to 0-7 for indexing."""
        return int(self.channel.get()) - 1  # Adjust channel number to 0-7 for indexing
