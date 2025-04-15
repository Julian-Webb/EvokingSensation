import logging
import time
import tkinter as tk
from tkinter import messagebox

from sciencemode import sciencemode as sm


class SerialPortError(Exception):
    """Exception raised for errors related to serial port operations."""
    pass


class StimulatorError(Exception):
    """Exception raised for errors related to stimulator operations."""
    pass


class Stimulator:
    MAX_WAIT_TIME_S = 1.0  # Timeout for waiting for device response

    def __init__(self, master: tk.Tk):
        self.master = master

        # Allocate memory for various structures used in communication with the device
        self.device = sm.ffi.new("Smpt_device*")  # memory for the device
        self.ack = sm.ffi.new("Smpt_ack*")  # memory for acknowledgment (responses)
        self.extended_version_ack = sm.ffi.new("Smpt_get_extended_version_ack*")  # memory for device info
        self.ml_update = sm.ffi.new("Smpt_ml_update*")  # memory for mid-level (ML) stimulation update
        self.ml_get_current_data = sm.ffi.new("Smpt_ml_get_current_data*")  # memory for getting current data

        self.keep_stimulating = False
        # The callback identifier which calls the _stimulation_loop after a certain duration
        self.stim_loop_callback = None
        self.start_time = None  # Initialize start time for stimulation

    def initialize(self, com_port: str):
        """
        Open the COM port and initialize the simulator.
        :param com_port: The COM port to open (e.g. "COM5").
        :return: The ``Smpt_device*`` object for further communication.
        """
        logging.info('--- Initialization ---')
        packet_number = self._open_com_port(com_port)

        self._log_version_info(packet_number)

        self._initialize_ml()  # Initialize mid-level (ML) stimulation

    def _open_com_port(self, com_port: str):
        com = sm.ffi.new("char[]", com_port.encode("ascii"))

        # Check if the serial port is available
        ret = sm.smpt_check_serial_port(com)
        logging.debug(f"Port check is {ret}")
        if not ret:
            msg = f"Failed to open the serial port {com_port}. \n(Port check is {ret})"
            logging.error(msg)
            raise SerialPortError(msg)

        # Open the serial port for communication with the device
        ret = sm.smpt_open_serial_port(self.device, com)
        if ret:
            logging.info(f"Serial port has been opened successfully.")

        # Generate the next packet number for communication (ensures synchronization with device)
        packet_number = sm.smpt_packet_number_generator_next(self.device)
        logging.debug(f"next packet_number {packet_number}")  # Output the next packet number
        return packet_number

    def _log_version_info(self, packet_number):
        # Send a request to get extended version information from the device
        ret = sm.smpt_send_get_extended_version(self.device, packet_number)
        logging.debug(f"smpt_send_get_extended_version: {ret}")  # Output the result of sending the request

        # Wait for a response packet from the device
        logging.debug("Waiting for device response.")
        start_time = time.time()

        while not sm.smpt_new_packet_received(self.device):
            # Check if the timeout has been reached
            if time.time() - start_time > self.MAX_WAIT_TIME_S:
                msg = f"Timeout waiting for device response. It took more than {self.MAX_WAIT_TIME_S} seconds."
                logging.error(msg)
                raise SerialPortError(msg)
            time.sleep(0.001)
        logging.info("Device response received.")

        # Get the last acknowledgment packet from the device
        sm.smpt_last_ack(self.device, self.ack)
        logging.debug(
            f"command number {self.ack.command_number}, packet_number {self.ack.packet_number}")  # Output command info

        # Retrieve the extended version information from the device
        ret = sm.smpt_get_get_extended_version_ack(self.device, self.extended_version_ack)
        logging.debug(f"smpt_get_get_extended_version_ack: {ret}")
        logging.debug(f"fw_hash: {self.extended_version_ack.fw_hash}")  # Output the firmware hash

        fw_version = self.extended_version_ack.uc_version.fw_version
        smpt_version = self.extended_version_ack.uc_version.smpt_version
        logging.debug(f"fw_version: {fw_version.major}.{fw_version.minor}.{fw_version.revision}")
        logging.debug(f"smpt_version: {smpt_version.major}.{smpt_version.minor}.{smpt_version.revision}")

    def _initialize_ml(self):
        """
        Initialize mid-level (ML) stimulation.
        """
        ml_init = sm.ffi.new("Smpt_ml_init*")
        ml_init.packet_number = sm.smpt_packet_number_generator_next(self.device)
        ret = sm.smpt_send_ml_init(self.device, ml_init)
        logging.debug(f"smpt_send_ml_init: {ret}")
        self.ml_update.packet_number = sm.smpt_packet_number_generator_next(self.device)
        time.sleep(0.001)  # TODO can I remove this?

    def rectangular_pulse(self, channel: int, amplitude_ma: float, pulse_width_us: int, inter_pulse_width_us: int,
                          period_ms: float):
        """
        Configure a rectangular pulse for the specified channel.
        """
        self.ml_update.enable_channel[channel] = True
        self.ml_update.channel_config[channel].period = period_ms  # Period in ms
        self.ml_update.channel_config[channel].number_of_points = 3
        self.ml_update.channel_config[channel].points[0].current = amplitude_ma
        self.ml_update.channel_config[channel].points[0].time = pulse_width_us
        self.ml_update.channel_config[channel].points[1].current = 0
        self.ml_update.channel_config[channel].points[1].time = inter_pulse_width_us
        self.ml_update.channel_config[channel].points[2].current = -amplitude_ma
        self.ml_update.channel_config[channel].points[2].time = pulse_width_us

    def stimulate_ml(self, stim_duration_s: float, on_termination: callable):
        """
        Start mid-level (ML) stimulation, send an update once per second, and stop after the specified duration.
        :param stim_duration_s: How long the stimulation should go on for in seconds
        # TODO will it really not be called?
        :param on_termination: The function to call when the stimulation terminates after the time runs out.
        This might not be called if the stimulation is terminated by other means.
        """
        self.start_time = time.perf_counter()
        ret = sm.smpt_send_ml_update(self.device, self.ml_update)  # This already starts the stimulation

        if ret:
            logging.info("Stimulation started successfully.")
            self.keep_stimulating = True
        else:
            msg = "Failed to start stimulation."
            logging.error(msg)
            raise StimulatorError(msg)

        # Let it loop but don't block the main thread
        self._stimulation_loop(stim_duration_s, on_termination)

        return self.start_time

    def _stimulation_loop(self, stim_duration_s: float, on_termination: callable):
        """Sends an update once per second to keep the stimulation running and stops after the specified time.
        :return: elapsed time in seconds"""

        elapsed_time = time.perf_counter() - self.start_time
        if self.keep_stimulating:
            self.ml_get_current_data.data_selection = sm.Smpt_Ml_Data_Channels
            self.ml_get_current_data.packet_number = sm.smpt_packet_number_generator_next(self.device)
            # We have to call this at least every 2s to keep the stimulation going
            ret = sm.smpt_send_ml_get_current_data(self.device, self.ml_get_current_data)
            logging.debug(f"smpt_send_ml_get_current_data: {ret}")

            # If we have more than 1.5s left of stimulation, we wait for 1s
            # Otherwise, we break out of the loop and wait for the remaining time
            # This is for precision as well as performance reasons: we can wait for the exact time, and we don't need to call
            # sm.smpt_send_ml_get_current_data that often.
            if elapsed_time < (stim_duration_s - 1.5):
                self.stim_loop_callback = self.master.after(1000, self._stimulation_loop, stim_duration_s,
                                                            on_termination)
            else:
                self.keep_stimulating = False
                remaining_time_ms = round((stim_duration_s - elapsed_time) * 1000)
                self.master.after(remaining_time_ms, self._stimulation_loop, stim_duration_s, on_termination)
        else:
            # We should only reach this after the time has run out. Otherwise, log this error.
            if elapsed_time < stim_duration_s:
                logging.warning("Stimulation time has not run out, but the stimulation is being stopped. "
                                "Something went wrong internally")
            self.stop_stimulation()
            on_termination()
        return elapsed_time

    def stop_stimulation(self):
        """
        Stop stimulation.
        :returns: whether stimulation was stopped successfully.
        """
        self.keep_stimulating = False

        # Cancel .after to stop recursively calling _stimulation_loop
        if self.stim_loop_callback is not None:
            self.master.after_cancel(self.stim_loop_callback)
            logging.info('Stimulation callback successfully canceled')

        packet_number = sm.smpt_packet_number_generator_next(self.device)
        ret = sm.smpt_send_ml_stop(self.device, packet_number)  # Stops the stimulation

        if ret:
            msg = 'Stimulation stopped successfully.'
            if self.start_time is not None:
                msg += f' Stimulation time: {time.perf_counter() - self.start_time:.5f} s'
            else:
                logging.debug('No start time recorded. Probably because stimulation was not started. '
                              'This piece of code should not be reached.')
            logging.info(msg)
        else:
            msg = "Failed to send stop signal to stimulator."
            logging.error(msg)
            messagebox.showerror(msg)
            raise StimulatorError(msg)

        return ret

    def close_com_port(self):
        """
        Close the COM port.
        """
        ret = sm.smpt_close_serial_port(self.device)
        if ret:
            logging.info("Serial port has been closed successfully.")
        else:
            msg = "Failed to close the serial port."
            logging.error(msg)
            raise SerialPortError(msg)
