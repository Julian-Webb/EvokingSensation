import logging
from collections import OrderedDict


class Settings:
    """Singleton Settings for the stimulation application.

    Attributes:
        amplitude_mA (float): The amplitude in mA.
        frequency_hz (float): The frequency in Hz.
        pulse_width_us (int): The pulse width in microseconds.
        inter_pulse_width_us (int): The time between the positive and negative phase of a pulse in microseconds.
        stim_duration_s (float): The stimulation duration in seconds.
        channel_input (int): The channel number (1-8). Refer to labels on device.
    """
    _instance = None

    PARAMETER_OPTIONS = OrderedDict(
        {
            'amplitude': {'label': 'Amplitude (mA)', 'range': (0.5, 15), 'increment': 0.5, 'numeric_type': float},
            'frequency': {'label': 'Frequency (Hz)', 'range': (1, 100), 'increment': 1, 'numeric_type': float},
            'pulse_width': {'label': 'Pulse Width (µs)', 'range': (1, 1000), 'increment': 10, 'numeric_type': int},
            'inter_pulse_width': {'label': 'Inter-Pulse Width (µs)', 'range': (1, 1000), 'increment': 10,
                                  'numeric_type': int},
            'stim_duration': {'label': 'Stimulation Duration (s)', 'range': (1, 240), 'increment': 1,
                              'numeric_type': float},
            'channel': {'label': 'Channel', 'range': (1, 8), 'increment': 1, 'numeric_type': int},
        }
    )

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Settings, cls).__new__(cls, *args, **kwargs)
            cls._instance.amplitude_mA = 2
            cls._instance.pulse_width_us = 100
            cls._instance.inter_pulse_width_us = 200
            cls._instance.stim_duration_s = 10
            cls._instance.channel_input = 1

            # TODO add com port as a setting?

            # Initialize frequency_hz with the setter, so that the period gets logged
            cls._instance._frequency_hz = None
            cls._instance.frequency_hz = 10

        return cls._instance

    @property
    def frequency_hz(self):
        return self._frequency_hz

    @frequency_hz.setter
    def frequency_hz(self, value):
        if value <= 0:
            raise ValueError("Frequency must be greater than 0.")
        self._frequency_hz = value

        logging.info(
            f'Period {self.period_ms} ms has been derived from frequency {self.frequency_hz} Hz')

    @property
    def period_ms(self):
        return (1 / self.frequency_hz) * 1000

    @property
    def channel_adjusted(self):
        """Adjusted channel number to 0-7 for indexing."""
        return self.channel_input - 1  # Adjust channel number to 0-7 for indexing
