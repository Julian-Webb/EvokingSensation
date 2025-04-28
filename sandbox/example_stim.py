import logging
import time

from stimulator import Stimulator
import tkinter as tk
from tkinter import ttk
logging.basicConfig(level=logging.DEBUG)

# --- Inputs ---
amplitude_mA: float = 50.0  # amplitude in mA
frequency_Hz = 10  # frequency in Hz
phase_duration = 100  # pulse width in microseconds
# inter pulse width in microseconds: the time between the positive and negative phase of a pulse
interphase_interval = 200
stim_duration_s = 100  # stimulation duration in seconds

# channel number (1-8). Refer to labels on device.
# This number will be adjusted to 0-7 in the code because indexing starts at 0.
channel_input = 1
# --- Derived variables ---
period_ms = (1 / frequency_Hz) * 1000
channel = channel_input - 1  # Adjust channel number to 0-7 for indexing

logging.info(f'Period {period_ms} ms has been derived from frequency {frequency_Hz} Hz')

# --- Variables ---
port = "COM5"

# --- The script ---
def stimulate():
    stimulator.initialize(port)

    # --- Pulse configuration ---
    # Configure a rectangular pulse for the specified channel.
    stimulator.rectangular_pulse(channel, amplitude_mA, phase_duration, interphase_interval, period_ms)

    # --- Stimulate ---
    stimulator.stimulate_ml(stim_duration_s, lambda: None)

    # --- Finalization ---
    time.sleep(stim_duration_s + 0.5)
    stimulator.close_com_port()

# --- Initialize device ---
root = tk.Tk()
root.geometry('200x100')

stimulator = Stimulator(root)
stim_button = ttk.Button(root, text='Stimulate',
                         command=stimulate)
stim_button.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

root.mainloop()