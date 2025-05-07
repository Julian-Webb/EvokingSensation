import logging
import time
from dataclasses import dataclass
import tkinter as tk
from tkinter import messagebox
from typing import Callable

from sciencemode import sciencemode as sm


@dataclass
class StimulationParameters:
    amplitude_ma: float
    phase_duration: int
    interpulse_interval: int
    period_ms: float


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
        self.ml_init = sm.ffi.new("Smpt_ml_init*")
        self.ml_update = sm.ffi.new("Smpt_ml_update*")  # memory for mid-level (ML) stimulation update
        self.ml_get_current_data = sm.ffi.new("Smpt_ml_get_current_data*")  # memory for getting current data
        self.ml_get_current_data_ack = sm.ffi.new("Smpt_ml_get_current_data_ack*")

        self.keep_stimulating = False
        # The callback identifier which calls the _stimulation_loop after a certain duration
        self.stim_loop_callback = None
        # The callback identifier which calls _check_for_error after a certain duration
        self.check_error_callback = None
        self.start_time = None  # start time of stimulation
        self._active_channels_adjusted = set()  # The active channels (adjusted for 0-indexing)

    def active_channels(self):
        """Get a set of the currently active channels as depicted on the stimulator."""
        return {x + 1 for x in self._active_channels_adjusted}  # adjust for 1-indexing

    def initialize(self, com_port: str):
        """
        Open the COM port and initialize the simulator.
        :param com_port: The COM port to open (e.g. "COM5").
        :return: The ``Smpt_device*`` object for further communication.
        """
        logging.info('--- Initialization ---')
        packet_number = self._open_com_port(com_port)

        self._log_version_info(packet_number)

    def _open_com_port(self, com_port: str):
        com = sm.ffi.new("char[]", com_port.encode("ascii"))

        # Check if the serial port is available
        ret = sm.smpt_check_serial_port(com)
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
        # logging.debug(f"next packet_number {packet_number}") # Output the next packet number
        return packet_number

    def _log_version_info(self, packet_number):
        # Send a request to get extended version information from the device
        _ret = sm.smpt_send_get_extended_version(self.device, packet_number)

        # Wait for a response packet from the device
        logging.debug("Waiting for device response...")
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

        # Output command info
        # logging.debug(f"command number {self.ack.command_number}, packet_number {self.ack.packet_number}")

        # Retrieve the extended version information from the device
        _ret = sm.smpt_get_get_extended_version_ack(self.device, self.extended_version_ack)
        # logging.debug(f"fw_hash: {self.extended_version_ack.fw_hash}") # Output the firmware hash

        fw_version = self.extended_version_ack.uc_version.fw_version
        smpt_version = self.extended_version_ack.uc_version.smpt_version
        logging.debug(f"fw_version: {fw_version.major}.{fw_version.minor}.{fw_version.revision}")
        logging.debug(f"smpt_version: {smpt_version.major}.{smpt_version.minor}.{smpt_version.revision}")

    def rectangular_pulse(self, channel: int, stim_params: StimulationParameters):
        """
        Configure a rectangular pulse for the specified channel using mid-level configuration.
        The pulse consists of three stages: a positive amplitude phase,
        an interpulse interval (zero amplitude), and a negative amplitude phase.
        This pulse is configured on the specified channel with specified timing
        and amplitude settings.

        :param channel: The channel number as depicted on the stimulator (1-8)
        :param stim_params: A StimulationParameters object with the amplitude, phase_duration, interpulse_interval, and period
        :return: None
        """
        channel_adjusted = channel - 1  # adjust channel for 0-indexing
        self._active_channels_adjusted.add(channel_adjusted)

        # configure
        self.ml_update.enable_channel[channel_adjusted] = True

        config = self.ml_update.channel_config[channel_adjusted]
        config.period = stim_params.period_ms
        config.number_of_points = 3
        config.points[0].current = stim_params.amplitude_ma
        config.points[0].time = stim_params.phase_duration
        config.points[1].current = 0
        config.points[1].time = stim_params.interpulse_interval
        config.points[2].current = -stim_params.amplitude_ma
        config.points[2].time = stim_params.phase_duration

    def _reset_pulse_configs(self):
        """Rests the pulse configurations to remove the previously specified pulses"""
        for channel in self._active_channels_adjusted:
            self.ml_update.enable_channel[channel] = False
        self._active_channels_adjusted.clear()

    def stimulate_ml(self, stim_duration_s: float, on_termination: Callable[[], None], on_error: Callable[[int], None]):
        """
        Start mid-level (ML) stimulation, send an update once per second, and stop after the specified duration.
        :param stim_duration_s: How long the stimulation should go on for in seconds
        :param on_termination: The function to call when the stimulation terminates after the time runs out.
        This might not be called if the stimulation is terminated by other means.
        :param on_error: A function to be executed if the stimulator says there's an error.
        :return: The start time of the stimulation.
        """
        logging.info('--- Stimulation ---')
        self._initialize_ml()  # Initialize mid-level (ML) stimulation

        logging.info(f'Stimulating on channels {self.active_channels()}')

        self.start_time = time.perf_counter()
        self.ml_update.packet_number = sm.smpt_packet_number_generator_next(self.device)
        ret = sm.smpt_send_ml_update(self.device, self.ml_update)  # This already starts the stimulation

        if ret:
            logging.info("Stimulation started successfully.")
            self.keep_stimulating = True
        else:
            msg = "Failed to start stimulation."
            logging.error(msg)
            raise StimulatorError(msg)

        # Let it loop but don't block the main thread
        self._stimulation_loop(stim_duration_s, on_termination, on_error)

        return self.start_time

    def _initialize_ml(self):
        """Initialize mid-level (ML) stimulation."""
        self.ml_init.packet_number = sm.smpt_packet_number_generator_next(self.device)
        ret = sm.smpt_send_ml_init(self.device, self.ml_init)
        logging.debug(f"smpt_send_ml_init: {ret}")
        # time.sleep(0.001)

    def _stimulation_loop(self, stim_duration_s: float, on_termination: Callable[[], None],
                          on_error: Callable[[int], None]):
        """Sends an update once per second to keep the stimulation running and stops after the specified time.
        :return: Elapsed time in seconds"""
        elapsed_time = time.perf_counter() - self.start_time

        if self.keep_stimulating:
            self.ml_get_current_data.data_selection = sm.Smpt_Ml_Data_Channels
            self.ml_get_current_data.packet_number = sm.smpt_packet_number_generator_next(self.device)
            # We have to call this at least every 2s to keep the stimulation going
            ret = sm.smpt_send_ml_get_current_data(self.device, self.ml_get_current_data)
            if ret:
                logging.debug(f"ML update sent. Elapsed time: {elapsed_time:.5f} s")
            else:
                logging.error(f"smpt_send_ml_get_current_data returned {ret}")

            # Check for errors asynchronously
            # 150 ms seems to give it enough time to receive a response consistently
            self.check_error_callback = self.master.after(150, self._check_for_error, on_error)

            # If we have more than 1.5 s left of stimulation, we wait for 1 s
            # Otherwise, we break out of the loop and wait for the remaining time
            # This is for precision as well as performance reasons: we can wait for the exact time, and we don't need to
            # call sm.smpt_send_ml_get_current_data that often.
            if elapsed_time < (stim_duration_s - 1.5):
                callback_after_ms = 1000
            else:
                self.keep_stimulating = False
                callback_after_ms = round((stim_duration_s - elapsed_time) * 1000)  # call back after the remaining time
            self.stim_loop_callback = self.master.after(callback_after_ms, self._stimulation_loop, stim_duration_s,
                                                        on_termination, on_error)
        else:
            # We should only reach this after the time has run out. Otherwise, log this error.
            if elapsed_time < stim_duration_s:
                logging.warning("Stimulation time has not run out, but the stimulation is being stopped. "
                                "Something went wrong internally")
            self.stop_stimulation()
            on_termination()
        return elapsed_time

    def _check_for_error(self, on_error: Callable[[int], None]):
        """Checks is the device is reporting an issue during stimulation."""
        # This code is copied and adapted from the notebook P24_ml_eight_channels.ipynb from the ScienceMode
        # python wrapper.
        # TODO adjust this whole function for multiple channels (check example notebook)
        self.ml_get_current_data_ack.packet_number = sm.smpt_packet_number_generator_next(self.device)
        while sm.smpt_new_packet_received(self.device):
            # Clear up the acknowledgment structure
            sm.smpt_clear_ack(self.ack)
            sm.smpt_last_ack(self.device, self.ack)

            # Check whether this packet is the acknowledgement for the ml_get_current_data command
            if self.ack.command_number != sm.Smpt_Cmd_Ml_Get_Current_Data_Ack:
                continue

            # Get the acknowledgement (response)
            ret = sm.smpt_get_ml_get_current_data_ack(self.device, self.ml_get_current_data_ack)
            if not ret:
                logging.debug(
                    f"Couldn't get the ml_get_current_data acknowledgement. (smpt_get_ml_get_current_data_ack: {ret})")

            # Check for an error on all active channels
            # TODO this hasn't been tested yet
            for channel_adj in self._active_channels_adjusted:
                error_on_channel = self.ml_get_current_data_ack.channel_data.channel_state[channel_adj]
                if bool(error_on_channel):
                    channel_input = channel_adj + 1  # adjust for 0-indexing
                    logging.error(f"There's an error on channel {channel_input}.")
                    on_error(channel_input)
                # else:
                #     # todo this else can be deleted later
                #     channel_input = channel_adj + 1
                #     logging.debug(f"No error on channel {channel_input}.")

    def stop_stimulation(self):
        """
        Stop stimulation.
        :returns: Whether stimulation was stopped successfully.
        """
        self.keep_stimulating = False
        # Cancel the callback to _stimulation_loop and _check_for_error
        if self.stim_loop_callback is not None:
            self.master.after_cancel(self.stim_loop_callback)
            # logging.debug(f'Called after_cancel for stimulation callback: {self.stim_loop_callback}')
            self.stim_loop_callback = None
        if self.check_error_callback is not None:
            self.master.after_cancel(self.check_error_callback)
            # logging.debug(f'Called after_cancel for check_error_callback: {self.check_error_callback}')
            self.check_error_callback = None
        self._reset_pulse_configs()

        packet_number = sm.smpt_packet_number_generator_next(self.device)
        ret = sm.smpt_send_ml_stop(self.device, packet_number)  # Stops the stimulation

        if ret:
            msg = 'Stimulation stopped successfully.'
            if self.start_time is not None:
                msg += f' Stimulation time: {time.perf_counter() - self.start_time:.5f} s'
            else:
                logging.warning('No start time recorded. Probably because stimulation was not started. '
                                'This piece of code should not be reached.')
            logging.info(msg)
        else:
            msg = "Failed to send stop signal to stimulator."
            logging.error(msg)
            messagebox.showerror(title='Stimulator Error', message=msg)
            raise StimulatorError(msg)

        return ret

    def close_com_port(self):
        """Close the COM port."""
        ret = sm.smpt_close_serial_port(self.device)
        if ret:
            logging.info("Serial port has been closed successfully.")
        else:
            msg = "Failed to close the serial port."
            logging.error(msg)
            raise SerialPortError(msg)
