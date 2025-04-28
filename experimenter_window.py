import logging
import time
import tkinter as tk
from tkinter import ttk, messagebox

from serial.tools import list_ports
from settings import Settings
from stimulator import Stimulator, SerialPortError


class ExperimenterWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Experimenter Window")

        # Define a custom style for the stop button
        style = ttk.Style()
        style.configure("EnabledStopButton.TButton", background="red", foreground="red")

        self.stimulator = Stimulator(self)

        # Create widgets
        self.parameter_manager = _ParameterManager(self)
        self.stimulation_buttons = _StimulationButtons(self, self.stimulator, self.on_start_stimulation,
                                                       self.on_stop_stimulation)
        self.com_port_manager = _ComPortManager(self, self.stimulator,
                                                on_successful_init=self.stimulation_buttons.enable_start,
                                                on_close_port=self.stimulation_buttons.disable_buttons)

        for frame in (self.com_port_manager, self.parameter_manager, self.stimulation_buttons):
            frame.pack(padx=10, pady=10)

    def on_start_stimulation(self):
        self.parameter_manager.set_state('disabled')
        self.com_port_manager.close_button['state'] = 'disabled'

    def on_stop_stimulation(self):
        self.parameter_manager.set_state('enabled')
        self.com_port_manager.close_button['state'] = 'normal'


class _ComPortManager(ttk.Frame):
    def __init__(self, master, stimulator: Stimulator, on_successful_init: callable, on_close_port: callable):
        """This class manages the COM port selection, opening, and closing.
        :param on_successful_init: A function to call if the COM port is successfully opened and mid-level stimulation was initialized"""
        super().__init__(master, borderwidth=2, relief="solid")
        self.stimulator = stimulator
        self.on_successful_init = on_successful_init
        self.on_close_port = on_close_port

        # Com port selection
        self.available_com_ports = []
        self.com_port = tk.StringVar()

        self.port_selector = ttk.Combobox(self,
                                          textvariable=self.com_port,
                                          values=self.available_com_ports,
                                          state='readonly')
        self.port_selector.pack(side="left", padx=5)
        # Initialize options and set default value
        self._update_available_com_ports()

        # Refresh button
        self.refresh_button = tk.Button(self, text="⭮", command=self._update_available_com_ports)
        self.refresh_button.pack(side="left", padx=5)

        # Open button
        self.open_button = tk.Button(self, text="Open", command=self.open_port)
        self.open_button.pack(side="left", padx=5)

        # Close button
        self.close_button = tk.Button(self, text="Close", state="disabled", command=self.close_port)
        self.close_button.pack(side="left", padx=5)

    def _update_available_com_ports(self):
        self.available_com_ports = sorted([port.device for port in list_ports.comports()])
        self.port_selector['values'] = self.available_com_ports

        if self.com_port.get() not in self.available_com_ports:
            if len(self.available_com_ports) > 0:
                self.com_port.set(self.available_com_ports[-1])
            else:
                raise Exception("No COM ports available")
        return list_ports.comports()

    def open_port(self):
        """Initialize the stimulator with the selected COM port, deactivate the Open button, activate the Close
        button, and call the function passed as on_successful_init at construction."""
        try:
            self.stimulator.initialize(self.com_port.get())
            self.port_selector.config(state='disabled')
            self.refresh_button.config(state="disabled")
            self.open_button.config(state="disabled")
            self.close_button.config(state="normal")
            self.on_successful_init()
        except SerialPortError as e:
            messagebox.showerror("Serial Port Error", str(e))

    def close_port(self):
        """Close the stimulator, activate the Open button, and deactivate the Close button"""
        try:
            self.stimulator.close_com_port()
            self.port_selector.config(state='normal')
            self.refresh_button.config(state="normal")
            self.open_button.config(state="normal")
            self.close_button.config(state="disabled")
            self.on_close_port()
        except SerialPortError as e:
            messagebox.showerror("Serial Port Error", str(e))


class _ParameterManager(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, borderwidth=2, relief="solid")
        self.spinboxes = {}

        # Create labels and spin boxes
        row = 0  # So PyCharm doesn't complain about the row possibly not being initialized below
        for row, parameter in enumerate(Settings.PARAMETER_OPTIONS):
            po = Settings.PARAMETER_OPTIONS[parameter]  # po = parameter options

            label = ttk.Label(self, text=po['label'])
            label.grid(row=row, column=0, padx=5, pady=5, sticky="w")

            # Validation command
            validation_cmd = (
                self.register(self._validate_input), "%P", po['range'][0], po['range'][1], po['numeric_type'])

            invalid_cmd = (self.register(self._on_invalid_input), parameter)
            spinbox = ttk.Spinbox(self,
                                  from_=po['range'][0], to=po['range'][1], increment=po['increment'],
                                  validate='focusout',
                                  validatecommand=validation_cmd,
                                  invalidcommand=invalid_cmd,
                                  textvariable=Settings().__getattribute__(parameter))
            spinbox.grid(row=row, column=1, padx=5, pady=5)

            self.spinboxes[parameter] = spinbox

        # Add the field to display the period
        row += 1
        ttk.Separator(self, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        period_label = ttk.Label(self, text="Period (ms)")
        period_label.grid(row=row + 1, column=0, padx=5, pady=5, sticky="w")
        period_field = ttk.Label(self, textvariable=Settings().period)
        period_field.grid(row=row + 1, column=1, padx=5, pady=5)

    @staticmethod
    def _on_invalid_input(parameter: str):
        """Handle invalid input by resetting value."""
        min_, max_ = Settings.PARAMETER_OPTIONS[parameter]['range']
        messagebox.showerror("Invalid Input",
                             f"Invalid input for {parameter}. Please enter a valid number between {min_} and {max_}.")

        str_var = Settings().__getattribute__(parameter)
        # Reset to default value
        str_var.set(Settings.PARAMETER_OPTIONS[parameter]['default'])

    @staticmethod
    def _validate_input(input_str: str, minimum: str, maximum: str, numeric_type: str):
        """Validate the input value based on the specified numeric type."""
        type_map = {"<class 'float'>": float, "<class 'int'>": int}
        numeric_class = type_map[numeric_type]
        try:
            # Try converting to the appropriate type. E.g., if the numeric_class is float, this would be calling
            # float(input_str)
            number = numeric_class(input_str)
        except ValueError:
            return False

        # check if it's in range
        return float(minimum) <= number <= float(maximum)

    def set_state(self, state: str):
        """
        Set the state of all child widgets in the frame.
        :param state: 'Normal' to enable, 'disabled' to disable.
        """
        for spinbox in self.spinboxes.values():
            spinbox.config(state=state)


# noinspection PyTypeChecker
class _Timer(ttk.Frame):
    """This class manages the timer for the stimulation duration."""

    def __init__(self, master):
        super().__init__(master, borderwidth=2, relief="solid")
        self.start_time = None
        self.keep_running = False  # Whether the timer should keep running

        self.timer_label = ttk.Label(self, text="Timer:")
        self.timer_label.pack(side="left", padx=5, pady=5)

        self.timer_var = tk.StringVar(self, value='00:00')
        self.duration_label = ttk.Label(self, textvariable=self.timer_var)
        self.duration_label.pack(side="left", padx=5, pady=5)

        self.unit_label = ttk.Label(self, text="s")
        self.unit_label.pack(side='right', padx=5, pady=5)

    def start_timer(self, start_time: float):
        """Start the timer with the given start time."""
        self.start_time = start_time
        self.keep_running = True
        self._update_timer()

    def _update_timer(self):
        """Update the timer display."""
        if self.keep_running:
            elapsed_time = time.perf_counter() - self.start_time
            self.timer_var.set(f"{elapsed_time:.2f}")
            self.after(10, self._update_timer)

    def stop_timer(self):
        """Stop the timer."""
        self.keep_running = False


class _StimulationButtons(ttk.Frame):
    def __init__(self, master, stimulator: Stimulator, on_start_callback: callable, on_stop_callback: callable, ):
        """The buttons to start and stop the stimulation
        :param on_start_callback: A function to call when stimulation was started successfully.
        :param on_stop_callback: A function to call when stimulation was stopped successfully.
        """
        super().__init__(master, borderwidth=2, relief="solid")
        self.stimulator = stimulator
        self.on_start_callback = on_start_callback
        self.on_stop_callback = on_stop_callback

        self.start_button = ttk.Button(self,
                                       text="Start Stimulation",
                                       state='disabled',
                                       command=self._on_start)

        self.start_button.grid(row=0, column=0, padx=5, pady=5)

        self.stop_button = ttk.Button(self, text='Stop Stimulation', state='disabled',
                                      command=self._on_manual_stop)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)

        self.timer = _Timer(self)
        self.timer.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

    def enable_start(self):
        """Enable the start button"""
        self.start_button['state'] = 'normal'

    def disable_buttons(self):
        """Disabled the start and stop buttons (for when the port is closed)."""
        self.start_button['state'] = 'disabled'
        self.stop_button['state'] = 'disabled'

    def _on_start(self):
        s = Settings()
        duration = float(Settings().stim_duration.get())

        # update the pulse configuration
        channel = s.channel_adjusted
        amplitude = float(s.amplitude.get())
        phase_duration = int(s.phase_duration.get())
        interpulse_interval = int(s.interpulse_interval.get())
        period = float(s.period.get())
        self.stimulator.rectangular_pulse(channel, amplitude, phase_duration, interpulse_interval, period)

        start_time = self.stimulator.stimulate_ml(duration, self._on_stimulation_finish, self._on_error)
        self.timer.start_timer(start_time)

        self.start_button['state'] = 'disabled'
        self.stop_button.config(state='normal', style='EnabledStopButton.TButton')
        self.on_start_callback()

    def _on_stimulation_finish(self):
        """What to always do when the stimulation finished."""
        self.timer.stop_timer()
        self.start_button['state'] = 'normal'
        self.stop_button.config(state='disabled', style='TButton')
        self.on_stop_callback()

    def _on_manual_stop(self):
        """What to do when the stop button is pressed."""
        self.stimulator.stop_stimulation()
        self._on_stimulation_finish()

    def _on_error(self, channel: int):
        """What to do if the stimulator responds with an error."""
        logging.debug('In _on_error')
        self.stimulator.stop_stimulation()
        self._on_stimulation_finish()
        messagebox.showerror(title="Stimulator Error.",
                             message=f"The stimulator has reported an error on channel {channel}. Stimulation stopped.")
