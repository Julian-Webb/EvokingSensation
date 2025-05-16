import time
from sciencemode import sciencemode as sm
from backend.utils import waiting_dots_animation

# --- Variables ---
port: bytes = b"COM5"

# --- Initialization (Boilerplate) ---
# Initialize communication with the device
ack = sm.ffi.new("Smpt_ack*")  # Allocate memory for acknowledgment
device = sm.ffi.new("Smpt_device*")  # Allocate memory for the device
extended_version_ack = sm.ffi.new("Smpt_get_extended_version_ack*")  # Memory for device info

# Specify the serial port for communication (e.g. COM5. Retrieve this from Windows device manager)
com = sm.ffi.new("char[]", port)

# Check if the serial port is available
ret = sm.smpt_check_serial_port(com)
print(f"Port check is {ret}")

# Open the serial port for communication with the device
ret = sm.smpt_open_serial_port(device, com)
print(f"smpt_open_serial_port: {ret}")

# Generate the next packet number for communication (ensures synchronization with device)
packet_number = sm.smpt_packet_number_generator_next(device)
print(f"next packet_number {packet_number}")  # Output the next packet number

# Send a request to get extended version information from the device
ret = sm.smpt_send_get_extended_version(device, packet_number)
print(f"smpt_send_get_extended_version: {ret}")  # Output the result of sending the request

ret = False

# Wait for a response packet from the device
print("Waiting for device response.", end='', flush=True)
while not sm.smpt_new_packet_received(device):
    waiting_dots_animation(1)
print("Done")

# Get the last acknowledgment packet from the device
sm.smpt_last_ack(device, ack)
print(f"command number {ack.command_number}, packet_number {ack.packet_number}")  # Output command info

# Retrieve the extended version information from the device
ret = sm.smpt_get_get_extended_version_ack(device, extended_version_ack)
print(f"smpt_get_get_extended_version_ack: {ret}")
print(f"fw_hash: {extended_version_ack.fw_hash}")  # Output the firmware hash

fw_version = extended_version_ack.uc_version.fw_version
smpt_version = extended_version_ack.uc_version.smpt_version
print(f"fw_version: {fw_version.major}.{fw_version.minor}.{fw_version.revision}")
print(f"smpt_version: {smpt_version.major}.{smpt_version.minor}.{smpt_version.revision}")
del fw_version, smpt_version

# --- Stimulation ---
print('\n--- Simulation ---')
# Initialize mid-level (ML) stimulation
ml_init = sm.ffi.new("Smpt_ml_init*")
ml_init.packet_number = sm.smpt_packet_number_generator_next(device)
ret = sm.smpt_send_ml_init(device, ml_init)
print(f"smpt_send_ml_init: {ret}")
time.sleep(1)

# Update mid-level (ML) stimulation configuration
max_current_mA = 5
pulse_width_us = 1000  # in micro-seconds
interphase_interval = 2000  # in micro-seconds
period_ms = 20  # in milliseconds
stim_duration_s = 5  # stimulation duration in seconds
# Duration of a point (~pulse width) can be between 0 and 4095 microseconds
# Current can be between -69 and 70 mA.*
# *According to the manual, it can be between -150 and 150 mA. However, the stimulator does not allow it.
# The current resolution is 0.5mA (according to the manual).

ml_update = sm.ffi.new("Smpt_ml_update*")
ml_update.packet_number = sm.smpt_packet_number_generator_next(device)

# --- Pulse configuration ---

channel = 0


# ml_update.enable_channel[channel] = True
# ml_update.channel_config[channel].period = 20 # Period in ms?
# ml_update.channel_config[channel].number_of_points = 6
# ml_update.channel_config[channel].points[0].current = max_current / 2
# ml_update.channel_config[channel].points[0].time = 50
# ml_update.channel_config[channel].points[1].current = max_current
# ml_update.channel_config[channel].points[1].time = 50
# ml_update.channel_config[channel].points[2].current = 0
# ml_update.channel_config[channel].points[2].time = 25
# ml_update.channel_config[channel].points[3].current = -(max_current / 4)
# ml_update.channel_config[channel].points[3].time = 50
# ml_update.channel_config[channel].points[4].current = -max_current
# ml_update.channel_config[channel].points[4].time = 25
# ml_update.channel_config[channel].points[5].current = 3.3
# ml_update.channel_config[channel].points[5].time = 50

# rectangular pulse
ml_update.enable_channel[channel] = True
ml_update.channel_config[channel].period = period_ms  # Period in ms
ml_update.channel_config[channel].number_of_points = 3
ml_update.channel_config[channel].points[0].current = max_current_mA
ml_update.channel_config[channel].points[0].time = pulse_width_us
ml_update.channel_config[channel].points[1].current = 0
ml_update.channel_config[channel].points[1].time = interphase_interval
ml_update.channel_config[channel].points[2].current = -max_current_mA
ml_update.channel_config[channel].points[2].time = pulse_width_us

# -------------------------


start_time = time.perf_counter()
ret = sm.smpt_send_ml_update(device, ml_update)
print(f"smpt_send_ml_update: {ret}")

ml_get_current_data = sm.ffi.new("Smpt_ml_get_current_data*")
while time.perf_counter() - start_time < stim_duration_s:
    # while True:
    ml_get_current_data.data_selection = sm.Smpt_Ml_Data_Channels
    ml_get_current_data.packet_number = sm.smpt_packet_number_generator_next(device)
    ret = sm.smpt_send_ml_get_current_data(device, ml_get_current_data)
    print(f"smpt_send_ml_get_current_data: {ret}")
    time.sleep(0.001)

packet_number = sm.smpt_packet_number_generator_next(device)
ret = sm.smpt_send_ml_stop(device, packet_number)
print(f"smpt_send_ml_stop: {ret}")

# --- Finalization ---
print('\n--- Finalization ---')
ret = sm.smpt_close_serial_port(device)
print(f"stimulation time: {time.perf_counter() - start_time:.5f} s")
print(f"smpt_close_serial_port: {ret}")
