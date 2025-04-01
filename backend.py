import logging
import stimulator
from sciencemode import sciencemode as sm
import time

logging.basicConfig(level=logging.INFO)

# --- Inputs ---
# TODO check inputs for validity. Period must be larger that pulse duration. Amplitude must be in range. Maybe more.
amplitude_mA = 2  # amplitude in mA
frequency_Hz = 10  # frequency in Hz
pulse_width_us = 100  # pulse width in microseconds
# inter pulse width in microseconds: the time between the positive and negative phase of a pulse
inter_pulse_width_us = 200
stim_duration_s = 10  # stimulation duration in seconds

# channel number (1-8). Refer to labels on device.
# This number will be adjusted to 0-7 in the code because indexing starts at 0.
channel_input = 7
# --- Derived variables ---
period_ms = (1 / frequency_Hz) * 1000
channel = channel_input - 1  # Adjust channel number to 0-7 for indexing

logging.info(f'Period {period_ms} ms has been derived from frequency {frequency_Hz} Hz')

# --- Variables ---
port: bytes = b"COM5"

# --- Initialize device ---
device = stimulator.initialize_stimulator(port)

# --- Stimulation ---
logging.info('--- Stimulation ---')

# Initialize mid-level (ML) stimulation.
stimulator.initialize_ml(device)

ml_update = sm.ffi.new("Smpt_ml_update*")
ml_update.packet_number = sm.smpt_packet_number_generator_next(device)

# --- Pulse configuration ---
# Configure a rectangular pulse for the specified channel.
stimulator.rectangular_pulse(ml_update, amplitude_mA, period_ms, pulse_width_us, inter_pulse_width_us, channel)

start_time = time.perf_counter()
# Inform the stimulator about the desired stimulation parameters.
ret = sm.smpt_send_ml_update(device, ml_update)  # This already starts the stimulation
logging.debug(f"smpt_send_ml_update: {ret}")

ml_get_current_data = sm.ffi.new("Smpt_ml_get_current_data*")
while True:
    ml_get_current_data.data_selection = sm.Smpt_Ml_Data_Channels
    ml_get_current_data.packet_number = sm.smpt_packet_number_generator_next(device)
    # We have to call this at least every 2s to keep the stimulation going
    ret = sm.smpt_send_ml_get_current_data(device, ml_get_current_data)
    logging.debug(f"smpt_send_ml_get_current_data: {ret}")

    # We stay in this loop as long as we have more than 1.5s left of stimulation
    # Then, we break out, wait for the remaining time and close the stimulator
    # This is for precision as well as performance reasons: we can wait for the exact time, and we don't need to call
    # sm.smpt_send_ml_get_current_data that often.
    if (time.perf_counter() - start_time) < (stim_duration_s - 1.5):
        time.sleep(1)
    else:
        break

# Wait for the remaining time
elapsed_time = time.perf_counter() - start_time
time.sleep(stim_duration_s - elapsed_time)
# Stop stimulation
packet_number = sm.smpt_packet_number_generator_next(device)
ret = sm.smpt_send_ml_stop(device, packet_number)
if ret:
    logging.info(f'Stimulation stopped successfully. Stimulation time: {time.perf_counter() - start_time:.5f} s')
else:
    logging.error('Failed to stop stimulation.')

# --- Finalization ---
logging.info('--- Finalization ---')
stimulator.close_stimulator(device)
