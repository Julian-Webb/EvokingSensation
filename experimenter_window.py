import tkinter as tk
from tkinter import ttk, messagebox

from serial.tools import list_ports

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

        # Example button
        button = tk.Button(self, text="Start Experiment", command=self.start_experiment)
        button.pack(pady=10)

    def start_experiment(self):
        print("Starting experiment...")  # Placeholder for actual experiment logic


class _ComPortManager(ttk.Frame):
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


class _ParameterManager(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, borderwidth=2, relief="solid")
        self.pack(pady=10, padx=10)

        # Example label
        label = tk.Label(self, text="Parameter Manager")
        label.pack(pady=10)
