import logging
import time
import tkinter as tk
import traceback
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Optional

from serial.tools import list_ports

from styling.app_style import AppStyle
from backend.participant_data import ParticipantData
from backend.locale_manager import LocaleManager
from widgets.participant_window import ParticipantWindow
from backend.settings import Settings
from backend.stimulation_order import StimulationOrder
from backend.stimulator import Stimulator, SerialPortError


class ExperimenterWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        # set up style
        self.style = AppStyle()

        self.participant_data = None

        self.title("Experimenter View")
        self.resizable(False, False)

        self.participant_window = None

        self.stimulator = Stimulator(self)

        # Create widgets
        self.stimulation_buttons = _StimulationButtons(self, self.stimulator, self.on_start_stimulation,
                                                       self.on_stop_stimulation)
        self.parameter_manager = _ParameterManager(self)
        self.com_port_manager = _ComPortManager(self, self.stimulator,
                                                on_successful_init=self.on_port_opened,
                                                on_close_port=self.on_port_closed)

        self.experiment_manager = _ExperimentManager(self, self.on_start_experiment, self.on_stop_experiment)

        for frame in (self.com_port_manager, self.stimulation_buttons, self.parameter_manager,
                      self.experiment_manager,):
            frame.pack(padx=10, pady=10)

        # self.com_port_manager.open_port()  # todo ON_LAUNCH delete
        # self.on_start_experiment(StimulationOrder.from_file(Settings().get_stim_order_path()))  # todo ON_LAUNCH delete

    def on_port_opened(self):
        """What to do when the port is successfully opened."""
        self.stimulation_buttons.enable_start()
        self.experiment_manager.enable_start()

    def on_port_closed(self):
        """What to do when the port is closed."""
        self.stimulation_buttons.disable_buttons()
        self.experiment_manager.disable_start()

    def on_start_any(self):
        """What to do when stimulation or experiment is started"""
        self.parameter_manager.set_state('disabled')
        self.com_port_manager.close_button['state'] = 'disabled'

    def on_stop_any(self):
        """What to do when stimulation or experiment is stopped"""
        self.parameter_manager.set_state('enabled')
        self.com_port_manager.close_button['state'] = 'normal'

    def on_start_stimulation(self):
        self.experiment_manager.disable_start()  # disable starting experiment
        self.on_start_any()

    def on_stop_stimulation(self):
        self.experiment_manager.enable_start()  # enable starting experiment
        self.on_stop_any()

    def on_start_experiment(self, stim_order: StimulationOrder):
        self.stimulation_buttons.disable_buttons()  # disable starting stimulation
        self.on_start_any()
        self.participant_data = ParticipantData()
        # open the participant window
        self.participant_window = ParticipantWindow(self, self.stimulator, stim_order, self.participant_data)

    def on_stop_experiment(self):
        self.stimulation_buttons.enable_start()  # enable starting stimulation
        self.on_stop_any()
        self.stimulator.stop_stimulation()
        self.participant_window.destroy()  # close the participant window
        self.participant_window = None


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
            self.port_selector.config(state='readonly')
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

        # title
        ttk.Label(self, text="Parameters", style='Heading3.TLabel').grid(row=0, column=0, columnspan=3, padx=5, pady=5)
        # Create labels and spin boxes
        row = 1
        for parameter in Settings.PARAMETER_OPTIONS:
            po = Settings.PARAMETER_OPTIONS[parameter]  # po = parameter options

            # parameter name label
            ttk.Label(self, text=po['label']).grid(row=row, column=0, padx=5, pady=5, sticky="w")
            # unit label
            ttk.Label(self, text=po['unit']).grid(row=row, column=2, pady=5, sticky="w")

            # Validation command
            validation_cmd = (
                self.register(self._validate_input), "%P", po['range'][0], po['range'][1], po['numeric_type'])

            invalid_cmd = (self.register(self._on_invalid_input), parameter)
            spinbox = ttk.Spinbox(self,
                                  width=10,
                                  from_=po['range'][0], to=po['range'][1], increment=po['increment'],
                                  validate='focusout',
                                  validatecommand=validation_cmd,
                                  invalidcommand=invalid_cmd,
                                  textvariable=Settings().__getattribute__(parameter))
            spinbox.grid(row=row, column=1, padx=5, pady=5)

            self.spinboxes[parameter] = spinbox
            row += 1

        # Add the field to display the period
        row += 1
        ttk.Separator(self, orient="horizontal").grid(row=row, column=0, columnspan=3, sticky="ew", pady=5)
        row += 1
        # period name label
        ttk.Label(self, text="Period").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        # period value label
        ttk.Label(self, textvariable=Settings().period_string_var).grid(row=row, column=1, padx=5, pady=5, sticky="w")
        # period unit label
        ttk.Label(self, text="ms").grid(row=row, column=2, pady=5, sticky="w")

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


class _Timer(ttk.Frame):
    """This class manages the timer for the stimulation duration."""

    def __init__(self, master):
        super().__init__(master)
        self.start_time = None
        self.keep_running = False  # Whether the timer should keep running

        self.timer_label = ttk.Label(self, text="Timer:")
        self.timer_label.pack(side="left", padx=5, pady=5)

        self.timer_var = tk.StringVar(self, value='00.00')
        self.duration_label = ttk.Label(self, textvariable=self.timer_var, style='Italic.TLabel')
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
            self.timer_var.set(f"{elapsed_time:05.2f}")
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

        self.title = ttk.Label(self, text="Test Stimulation", style='Heading3.TLabel')
        self.title.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        self.start_button = ttk.Button(self, text="▶ Start Stimulation", state='disabled', command=self._on_start)

        self.start_button.grid(row=1, column=0, padx=5, pady=5)

        self.stop_button = ttk.Button(self, text='🟥 Stop Stimulation', state='disabled', command=self._on_manual_stop)
        self.stop_button.grid(row=1, column=1, padx=5, pady=5)

        self.timer = _Timer(self)
        self.timer.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

    def enable_start(self):
        """Enable the start button"""
        self.start_button['state'] = 'normal'

    def disable_buttons(self):
        """Disabled the start and stop buttons (for when the port is closed)."""
        self.start_button['state'] = 'disabled'
        self.stop_button['state'] = 'disabled'

    def _on_start(self):
        s = Settings()
        # update the pulse configuration
        self.stimulator.rectangular_pulse(s.channel.get(), s.get_stimulation_parameters())

        start_time = self.stimulator.stimulate_ml(s.stim_duration.get(), self._on_stimulation_finish, self._on_error)
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
        logging.debug(f'A stimulation error occurred on channel {channel}')
        self._on_stimulation_finish()
        messagebox.showerror(title="Stimulator Error.",
                             message=f"The stimulator has reported an error on channel {channel}. Stimulation stopped.")


class _ExperimentManager(ttk.Frame):
    def __init__(self, master, on_start_experiment: Callable[[StimulationOrder], None],
                 on_stop_experiment_callback: Callable):
        super().__init__(master, borderwidth=2, relief="solid")
        self.on_start_experiment = on_start_experiment
        self.on_stop_experiment_callback = on_stop_experiment_callback

        self.title = ttk.Label(self, text="Experiment", style='Heading3.TLabel')

        # set up localization (different languages for the participant window)
        self.locale_manager = LocaleManager()
        self.language_var = tk.StringVar(value=self.locale_manager.current_locale.display_name)
        self.locale_selector = ttk.Combobox(self, textvariable=self.language_var, state='readonly',
                                            values=[locale.display_name for locale in
                                                    self.locale_manager.available_locales])

        # Directory selector for participant data
        folder_frame = tk.Frame(self)
        # folder label
        ttk.Label(folder_frame, text="Participant Data Folder:").grid(row=0, column=0, columnspan=2, padx=5,
                                                                      pady=(5, 0))
        # folder entry field
        self.folder_entry = tk.Entry(folder_frame, textvariable=Settings().participant_folder_var, width=40)
        self.folder_entry.icursor(tk.END)  # Move caret to end
        self.folder_entry.xview_moveto(1)  # Scroll so the end is visible
        self.folder_entry.grid(row=1, column=0, padx=5, pady=(0, 5))
        # browse button
        tk.Button(folder_frame, text='📁', command=self.select_participant_folder).grid(row=1, column=1)

        # Start and stop buttons
        self.start_exp_button = ttk.Button(self, text='▶ Start Experiment', state='disabled', command=self.on_start)
        self.stop_exp_button = ttk.Button(self, text='🟥 Stop Experiment', state='disabled', command=self.on_stop)

        self.title.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        self.locale_selector.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        folder_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        self.start_exp_button.grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.stop_exp_button.grid(row=3, column=1, padx=5, pady=5, sticky='w')

    def enable_start(self):
        self.start_exp_button['state'] = 'normal'

    def disable_start(self):
        self.start_exp_button['state'] = 'disabled'

    def on_start(self):
        """Start the experiment."""
        possible_stim_order = self.validate_participant_folder()
        if possible_stim_order is not None:
            # Set the locale for the new window
            self.locale_manager.set_locale(self.language_var.get())
            self.locale_selector['state'] = 'disabled'

            # If we reach this possible_stim_order will contain a proper StimulationOrder
            self.on_start_experiment(possible_stim_order)
            self.start_exp_button['state'] = 'disabled'
            self.stop_exp_button.config(state='normal', style='EnabledStopButton.TButton')

    def on_stop(self):
        self.on_stop_experiment_callback()
        self.locale_selector['state'] = 'readonly'
        self.start_exp_button['state'] = 'normal'
        self.stop_exp_button.config(state='disabled', style='TButton')

    def select_participant_folder(self):
        """Open a file dialog to select a folder for participant data."""
        folder_name = filedialog.askdirectory(title='Select participant data folder')
        if folder_name:
            Settings().participant_folder_var.set(folder_name)
        self.folder_entry.icursor(tk.END)  # Move caret to end
        self.folder_entry.xview_moveto(1)  # Scroll so the end is visible

    @staticmethod
    def validate_participant_folder() -> Optional[StimulationOrder]:
        """Check if the participant folder contains the necessary files (stimulation order and potentially calibration order).
        :return: The StimulationOrder if it could be read. None otherwise."""
        # todo ON_LAUNCH add calibration order if necessary
        s = Settings()
        # noinspection PyBroadException
        try:
            stim_order = StimulationOrder.from_file(s.get_stim_order_path())
            return stim_order
        except FileNotFoundError:
            messagebox.showerror("File Not Found",
                                 f"The stimulation order file '{s.get_stim_order_path()}' was not found in the given directory.")
            return None
        except Exception:
            messagebox.showerror("File Error",
                                 f"There was an error regarding the stimulation order in the given directory:\n\n{traceback.format_exc()}")
            return None
