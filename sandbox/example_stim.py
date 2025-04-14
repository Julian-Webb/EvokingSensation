import logging
from stimulator import Stimulator
logging.basicConfig(level=logging.DEBUG)

# --- Inputs ---
# TODO check inputs for validity. Period must be larger that pulse duration. Amplitude must be in range. Maybe more.
amplitude_mA: float = 65  # amplitude in mA
frequency_Hz = 10  # frequency in Hz
pulse_width_us = 360  # pulse width in microseconds
# inter pulse width in microseconds: the time between the positive and negative phase of a pulse
inter_pulse_width_us = 200
stim_duration_s = 10  # stimulation duration in seconds

# channel number (1-8). Refer to labels on device.
# This number will be adjusted to 0-7 in the code because indexing starts at 0.
channel_input = 1
# --- Derived variables ---
period_ms = (1 / frequency_Hz) * 1000
channel = channel_input - 1  # Adjust channel number to 0-7 for indexing

logging.info(f'Period {period_ms} ms has been derived from frequency {frequency_Hz} Hz')

# --- Variables ---
port = "COM5"

# --- Initialize device ---
stimulator = Stimulator()
stimulator.initialize(port)

# --- Pulse configuration ---
# Configure a rectangular pulse for the specified channel.
stimulator.rectangular_pulse(amplitude_mA, period_ms, pulse_width_us, inter_pulse_width_us, channel)

# --- Stimulate ---
stimulator.stimulate_ml(stim_duration_s)

# --- Finalization ---
stimulator.close_com_port()
