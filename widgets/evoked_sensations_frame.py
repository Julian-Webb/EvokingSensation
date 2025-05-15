import sys

import tkinter as tk
from tkinter import ttk
from typing import Callable, Any

from .location_inputter import LocationInputter, LocationType
import gettext
_ = gettext.gettext  # todo does this break everything?

class _SingleSensationFrame(tk.Frame):
    SENSATION_TYPES = ['Touch', 'Pulse', 'Tingling', 'Vibration', 'Cramp', 'Pain', 'Heat', 'Cold', 'Other']
    INTENSITY_OPTIONS = [i for i in range(1, 11)]
    LOCATIONS = ['D1', 'D2', 'D3', 'D4', 'S1', 'S2', 'S3', 'S4', 'S5', 'Calf', 'Shin']

    # noinspection PyUnreachableCode
    if False:  # Just so gettext realizes that these strings need to be translated
        _('Calf')
        _('Shin')
        _('Touch')
        _('Pulse')
        _('Tingling')
        _('Vibration')
        _('Cramp')
        _('Pain')
        _('Heat')
        _('Cold')
        _('Other')

    def __init__(self, master, sensation_number: int, on_remove: Callable, on_input_callback: Callable):
        """A Frame which lets the participant input information for a single sensation.
        :param master: The parent widget.
        :param sensation_number: The number of the sensation.
        :param on_remove: A function to call when the sensation is removed."""
        super().__init__(master, borderwidth=1, relief="solid")

        # Initialize tkinter vars for inputs
        self.type_var = tk.StringVar(self)
        self.intensity_var = tk.IntVar(self)
        self.location_vars = {location: tk.BooleanVar(self, value=False) for location in self.LOCATIONS}

        # Link changes in the variables to on_input_callback
        for var in [self.type_var, self.intensity_var] + list(self.location_vars.values()):
            print(var)
            var.trace_add('write', on_input_callback)

        # Header Frame (first row)
        header_frame = ttk.Frame(self)  # The frame at the top of this Widget
        header_frame.columnconfigure(0, weight=1)
        self.title_label = ttk.Label(header_frame, text=_('Sensation {}').format(sensation_number), font='bold')
        self.title_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        remove_button = ttk.Button(header_frame, text=_('- Remove sensation'), command=lambda: on_remove(self))
        remove_button.grid(row=0, column=1, padx=5, pady=5, sticky="e")

        # Sensation Type Frame
        type_frame = ttk.Frame(self)
        type_label = ttk.Label(type_frame, text=_('Type:'))
        type_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Radio buttons for type
        for idx, sens_type in enumerate(self.SENSATION_TYPES):
            ttk.Radiobutton(type_frame, variable=self.type_var, text=_(sens_type), value=sens_type
                            ).grid(row=0, column=idx + 1, padx=5, pady=5)

        # Sensation Intensity Frame
        intensity_frame = ttk.Frame(self)
        intensity_label = ttk.Label(intensity_frame, text=_('Intensity:'))
        intensity_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        # Radiobuttons for intensity
        for idx, intensity in enumerate(self.INTENSITY_OPTIONS):
            ttk.Radiobutton(intensity_frame, text=str(intensity), variable=self.intensity_var, value=intensity
                            ).grid(row=0, column=idx + 1, padx=5, pady=(5, 0))
        # labels for intensity
        ttk.Label(intensity_frame, text=_('Mild'), anchor='center').grid(row=1, column=1, columnspan=3,
                                                                         sticky='ew')
        ttk.Label(intensity_frame, text=_('Moderate'), anchor='center').grid(row=1, column=4, columnspan=4,
                                                                             sticky='ew')
        ttk.Label(intensity_frame, text=_('Strong'), anchor='center').grid(row=1, column=8, columnspan=3,
                                                                           sticky='ew')

        # location frame
        location_frame = ttk.Frame(self)
        location_label = ttk.Label(location_frame, text=_('Location:'))
        location_label.grid(row=0, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="w")

        # Make inputters for foot and leg
        foot = LocationInputter(location_frame, LocationType.FOOT, self.location_vars, scaling=0.4)
        leg = LocationInputter(location_frame, LocationType.LEG, self.location_vars, scaling=0.4)
        foot.grid(row=1, column=0, padx=5, pady=5)
        leg.grid(row=1, column=1, padx=5, pady=5)

        # Put all the frames together
        for frame in [header_frame, type_frame, intensity_frame, location_frame]:
            frame.pack(fill='x', expand=True, padx=5, pady=5)

    def get_sensation_data(self) -> dict[str, Any]:
        """Access the data the participant has input for this sensation.
        :returns: A dict with the entries 'type', 'intensity', and 'locations'."""
        locations = [loc for loc in self.LOCATIONS if self.location_vars[loc].get()]
        return {'type': self.type_var.get(), 'intensity': self.intensity_var.get(), 'locations': locations}

    def all_inputs_filled(self) -> bool:
        """Check if all inputs have been filled in."""
        return self.type_var.get() != '' and self.intensity_var.get() != '' and any(
            self.location_vars[loc].get() for loc in self.LOCATIONS)


class EvokedSensationsFrame(tk.Frame):
    def __init__(self, master: tk.Widget, on_continue: Callable[[list[dict[str, Any]]], None], trial_number: int):
        """The Frame where the participant can add multiple evoked sensations and continue stimulation.
        :param master: The parent widget.
        :param on_continue: A function to call the participant presses continue.
        :param trial_number: The current trial number."""
        super().__init__(master)
        self.on_continue = on_continue

        # The canvas is just here to enable scrolling and only contains the main_frame
        self.canvas = tk.Canvas(self)
        self.canvas.grid(row=0, column=0, sticky='nsew')

        scrollbar = tk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # link canvas and scrollbar
        self.canvas.configure(yscrollcommand=scrollbar.set)
        # Make the entire canvas scrollable
        self.canvas.bind('<Configure>', self._on_canvas_resize)

        # The main_frame contains all content except the scrollbar
        self.main_frame = ttk.Frame(self.canvas)
        self._create_main_content(trial_number)

        # resize the scroll region when the main_frame changes size (because sensations are added / removed)
        self.main_frame.bind('<Configure>', self._on_frame_configure)
        self.window_id = self.canvas.create_window((self.canvas.winfo_reqwidth() / 2, 0), window=self.main_frame,
                                                   anchor='n')

        if sys.platform == 'darwin':  # mac
            on_mousewheel = self._on_mousewheel_mac
        elif sys.platform.startswith('win'):  # windows
            on_mousewheel = self._on_mousewheel_windows
        else:
            raise NotImplementedError(f"Unsupported platform: {sys.platform}")
        self.canvas.bind_all("<MouseWheel>", on_mousewheel)

    def _create_main_content(self, trial_number):
        """Must be called during initialization to create the main content of the Frame."""
        # Header Frame
        header_frame = tk.Frame(self.main_frame)
        header_frame.columnconfigure(0, weight=1)
        title = ttk.Label(header_frame, text=_('Evoked Sensations'), font='bold')
        trial_number_label = ttk.Label(header_frame, text=_('Trial {}').format(trial_number))
        title.grid(row=0, column=0, sticky="w")
        trial_number_label.grid(row=0, column=1, sticky="e")

        # Frame for all evoked sensations
        self.sensations_container = tk.Frame(self.main_frame)
        self.no_sensations_label = ttk.Label(self.sensations_container,
                                             text=_(
                                                 'If you felt a sensation, please add it.\nOtherwise, continue stimulation.'),
                                             font='bold')
        self.no_sensations_label.pack(padx=5, pady=5)
        self.sensations_frames = []

        # Add sensation button
        add_sensation_button = ttk.Button(self.main_frame, text=_('+ Add Sensation'), command=self.add_sensation)

        # Continue button
        self.continue_button = ttk.Button(self.main_frame, text=_('Continue Stimulation'),
                                          command=self.get_sensations_and_continue)

        header_frame.pack(fill='x', expand=True, padx=5, pady=5)
        self.sensations_container.pack(padx=5, pady=5)
        add_sensation_button.pack()
        self.continue_button.pack()

    def _on_mousewheel_windows(self, event):
        self.canvas.yview_scroll(-1 * int(event.delta // 120), "units")

    def _on_mousewheel_mac(self, event):
        self.canvas.yview_scroll(-1 * int(event.delta), "units")

    def _on_canvas_resize(self, event):
        """Handle the canvas resize events by re-centering the frame inside"""
        canvas_width = event.width
        self.canvas.coords(self.window_id, canvas_width / 2, 0)  # Keep y at 0

    def _on_frame_configure(self, event):
        """Update the scroll region when the frame changes size"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # Ensure the frame width matches the canvas
        canvas_width = self.canvas.winfo_width()
        if canvas_width > 1:  # Ensure canvas has been drawn
            self.canvas.itemconfig(self.window_id, width=canvas_width)

    def add_sensation(self):
        # Remove no_sensations_label if it was there before
        if len(self.sensations_frames) == 0:
            self.no_sensations_label.pack_forget()

        new_sensation = _SingleSensationFrame(self.sensations_container, len(self.sensations_frames) + 1,
                                              self.remove_sensation, self.check_complete_inputs)
        self.sensations_frames.append(new_sensation)
        new_sensation.pack(padx=5, pady=5)

        # Disabled continue button because you should only be able to continue when all inputs have been filled in
        self.continue_button.config(state='disabled')

    def remove_sensation(self, query_sensation_frame):
        self.sensations_frames.remove(query_sensation_frame)
        query_sensation_frame.pack_forget()
        query_sensation_frame.destroy()

        # Update indexes of remaining sensations
        for i, sensation_frame in enumerate(self.sensations_frames):
            sensation_frame.title_label.config(text=_('Sensation {}').format(i + 1))

        # Show no_sensations_label if necessary
        if len(self.sensations_frames) == 0:
            self.no_sensations_label.pack(padx=5, pady=5)

    def check_complete_inputs(self, *args):
        """Enable the continue button if all sensations have been filled in and disable if not.
        Should be called every time an input is given."""
        # Check if all inputs have been provided
        for sensation in self.sensations_frames:
            if not sensation.all_inputs_filled():
                self.continue_button.config(state='disabled')
                return
        self.continue_button.config(state='normal')

    def get_sensations_and_continue(self):
        data = []
        for sensation in self.sensations_frames:
            data.append(sensation.get_sensation_data())
        self.on_continue(data)
