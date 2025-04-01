import logging
import time
from sciencemode import sciencemode as sm


def initialize_stimulator(com_port: bytes):
    """
    Open the COM port and initialize the simulator.
    """
    logging.info('--- Initialization ---')
    # Initialize communication with the device
    ack = sm.ffi.new("Smpt_ack*")  # Allocate memory for acknowledgment
    device = sm.ffi.new("Smpt_device*")  # Allocate memory for the device
    extended_version_ack = sm.ffi.new("Smpt_get_extended_version_ack*")  # Memory for device info

    # Specify the serial port for communication (e.g. COM5. Retrieve this from Windows device manager)
    com = sm.ffi.new("char[]", com_port)

    # Check if the serial port is available
    ret = sm.smpt_check_serial_port(com)
    logging.debug(f"Port check is {ret}")

    # Open the serial port for communication with the device
    ret = sm.smpt_open_serial_port(device, com)
    if ret: logging.info(f"Serial port has been opened successfully.")

    # Generate the next packet number for communication (ensures synchronization with device)
    packet_number = sm.smpt_packet_number_generator_next(device)
    logging.debug(f"next packet_number {packet_number}")  # Output the next packet number

    # Send a request to get extended version information from the device
    ret = sm.smpt_send_get_extended_version(device, packet_number)
    logging.debug(f"smpt_send_get_extended_version: {ret}")  # Output the result of sending the request

    # Wait for a response packet from the device
    logging.debug("Waiting for device response.")
    while not sm.smpt_new_packet_received(device):
        time.sleep(1)
    logging.info("Device response received.")

    # Get the last acknowledgment packet from the device
    sm.smpt_last_ack(device, ack)
    logging.debug(f"command number {ack.command_number}, packet_number {ack.packet_number}")  # Output command info

    # Retrieve the extended version information from the device
    ret = sm.smpt_get_get_extended_version_ack(device, extended_version_ack)
    logging.debug(f"smpt_get_get_extended_version_ack: {ret}")
    logging.debug(f"fw_hash: {extended_version_ack.fw_hash}")  # Output the firmware hash

    fw_version = extended_version_ack.uc_version.fw_version
    smpt_version = extended_version_ack.uc_version.smpt_version
    logging.debug(f"fw_version: {fw_version.major}.{fw_version.minor}.{fw_version.revision}")
    logging.debug(f"smpt_version: {smpt_version.major}.{smpt_version.minor}.{smpt_version.revision}")

    return device


def initialize_ml(device):
    """
    Initialize mid-level (ML) stimulation.
    """
    ml_init = sm.ffi.new("Smpt_ml_init*")
    ml_init.packet_number = sm.smpt_packet_number_generator_next(device)
    ret = sm.smpt_send_ml_init(device, ml_init)
    logging.debug(f"smpt_send_ml_init: {ret}")
    time.sleep(0.5)


def rectangular_pulse(ml_update, amplitude_mA, period_ms, pulse_width_us, inter_pulse_width_us, channel):
    """
    Configure a rectangular pulse for the specified channel.
    """
    ml_update.enable_channel[channel] = True
    ml_update.channel_config[channel].period = period_ms  # Period in ms
    ml_update.channel_config[channel].number_of_points = 3
    ml_update.channel_config[channel].points[0].current = amplitude_mA
    ml_update.channel_config[channel].points[0].time = pulse_width_us
    ml_update.channel_config[channel].points[1].current = 0
    ml_update.channel_config[channel].points[1].time = inter_pulse_width_us
    ml_update.channel_config[channel].points[2].current = -amplitude_mA
    ml_update.channel_config[channel].points[2].time = pulse_width_us


def close_stimulator(device):
    """
    Close the COM port and clean up.
    """
    ret = sm.smpt_close_serial_port(device)
    if ret:
        logging.info("Serial port has been closed successfully.")
    else:
        logging.error("Failed to close the serial port.")