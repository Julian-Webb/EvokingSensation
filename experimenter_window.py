import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Union

from serial.tools import list_ports
from settings import Settings
from stimulator import Stimulator, SerialPortError


class ExperimenterWindow(tk.Tk):
    def __init__(self, stimulator: Stimulator):
        super().__init__()
        self.stimulator = stimulator

        self.title("Experimenter Window")
        self.geometry("800x600")

        # Create widgets
        self.create_widgets()

    def create_widgets(self):
        # Example label
        com_port_manager = _ComPortManager(self, self.stimulator)
        com_port_manager.pack(pady=10, padx=10)

        parameter_manager = _ParameterManager(self)
        parameter_manager.pack(pady=10, padx=10)


class _ComPortManager(ttk.Frame):
    """This class manages the COM port selection, opening and closing."""

    def __init__(self, parent, stimulator: Stimulator):
        super().__init__(parent, borderwidth=2, relief="solid")
        self.stimulator = stimulator

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
        self.open_button = tk.Button(self, text="Open & Initialize", command=self.open_and_initialize)
        self.open_button.pack(side="left", padx=5)

        # Close button
        self.close_button = tk.Button(self, text="Close", state="disabled", command=self.close)
        self.close_button.pack(side="left", padx=5)

    def _update_available_com_ports(self):
        self.available_com_ports = sorted([port.device for port in list_ports.comports()])
        self.port_selector['values'] = self.available_com_ports

        if self.com_port.get() not in self.available_com_ports:
            if len(self.available_com_ports) > 0:
                self.com_port.set(self.available_com_ports[0])
            else:
                raise Exception("No COM ports available")
        return list_ports.comports()

    def open_and_initialize(self):
        """Initialize the stimulator with the selected COM port, deactivate the Open button and activate the Close
        button"""
        try:
            self.stimulator.initialize(self.com_port.get())
            self.port_selector.config(state='disabled')
            self.refresh_button.config(state="disabled")
            self.open_button.config(state="disabled")
            self.close_button.config(state="normal")

        except SerialPortError as e:
            messagebox.showerror("Serial Port Error", str(e))

    def close(self):
        """Close the stimulator, activate the Open button and deactivate the Close button"""
        try:
            self.stimulator.close_com_port()
            self.port_selector.config(state='normal')
            self.refresh_button.config(state="normal")
            self.open_button.config(state="normal")
            self.close_button.config(state="disabled")
        except SerialPortError as e:
            messagebox.showerror("Serial Port Error", str(e))


NUMERIC = Union[int, float]


class _ParameterManager(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, borderwidth=2, relief="solid")

        # Create labels and spin boxes
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
            # Try converting to the appropriate type. E.g. if the numeric_class is float, this would be calling
            # float(input_str)
            number = numeric_class(input_str)
        except ValueError:
            return False

        # check if it's in range
        return float(minimum) <= number <= float(maximum)
