import sys

import tkinter as tk
from tkinter import ttk
from typing import Callable, Any

from .location_inputter import LocationInputter, LocationType


class _SingleSensationFrame(tk.Frame):
    SENSATION_TYPES = ['Touch', 'Pulse', 'Tingling', 'Vibration', 'Cramp', 'Pain', 'Heat', 'Cold', 'Other']
    INTENSITY_OPTIONS = [i for i in range(1, 11)]
    LOCATIONS = ['D1', 'D2', 'D3', 'D4', 'S1', 'S2', 'S3', 'S4', 'S5', 'calf', 'shin']

    def __init__(self, master, sensation_number: int, on_remove):
        """A Frame which lets the participant input information for a single sensation.
        :param master: The parent widget.
        :param sensation_number: The number of the sensation.
        :param on_remove: A function to call when the sensation is removed."""
        super().__init__(master, highlightbackground='blue', highlightthickness=2,)

        # Initialize tkinter vars for inputs
        self.type_var = tk.StringVar(self)
        self.intensity_var = tk.IntVar(self)
        self.location_vars = {location: tk.BooleanVar(self, value=False) for location in self.LOCATIONS}

        # Header Frame (first row)
        header_frame = ttk.Frame(self)  # The frame at the top of this Widget
        header_frame.columnconfigure(0, weight=1)
        self.title_label = ttk.Label(header_frame, text=f'Sensation {sensation_number}', font='bold')
        self.title_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        remove_button = ttk.Button(header_frame, text='- Remove sensation', command=lambda: on_remove(self))
        remove_button.grid(row=0, column=1, padx=5, pady=5, sticky="e")

        # Sensation Type Frame
        type_frame = ttk.Frame(self)
        type_label = ttk.Label(type_frame, text='Type:')
        type_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Radio buttons for type
        for idx, sens_type in enumerate(self.SENSATION_TYPES):
            ttk.Radiobutton(type_frame, text=sens_type, variable=self.type_var, value=sens_type
                            ).grid(row=0, column=idx + 1, padx=5, pady=5)

        # Sensation Intensity Frame
        intensity_frame = ttk.Frame(self)
        intensity_label = ttk.Label(intensity_frame, text='Intensity:')
        intensity_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        # Radiobuttons for intensity
        for idx, intensity in enumerate(self.INTENSITY_OPTIONS):
            ttk.Radiobutton(intensity_frame, text=str(intensity), variable=self.intensity_var, value=intensity
                            ).grid(row=0, column=idx + 1, padx=5, pady=(5, 0))
        # labels for intensity
        ttk.Label(intensity_frame, text='Mild', anchor='center').grid(row=1, column=1, columnspan=3,
                                                                      sticky='ew')
        ttk.Label(intensity_frame, text='Moderate', anchor='center').grid(row=1, column=4, columnspan=4,
                                                                          sticky='ew')
        ttk.Label(intensity_frame, text='Strong', anchor='center').grid(row=1, column=8, columnspan=3,
                                                                        sticky='ew')

        # location frame
        location_frame = ttk.Frame(self)
        location_label = ttk.Label(location_frame, text='Location:')
        location_label.grid(row=0, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="w")

        # Make inputters for foot and leg
        foot = LocationInputter(location_frame, LocationType.FOOT, self.location_vars, scaling=0.3)
        leg = LocationInputter(location_frame, LocationType.LEG, self.location_vars, scaling=0.3)
        foot.grid(row=1, column=0, padx=5, pady=5)
        leg.grid(row=1, column=1, padx=5, pady=5)

        # Put all the frames together
        for frame in [header_frame, type_frame, intensity_frame, location_frame]:
            frame.pack(fill='x', expand=True, padx=5, pady=5)

    def get_sensation_data(self):
        """Access the data the participant has input for this sensation.
        :returns: A dict with the entries 'type', 'intensity', and 'locations'."""
        locations = [loc for loc in self.LOCATIONS if self.location_vars[loc].get()]
        return {'type': self.type_var.get(), 'intensity': self.intensity_var.get(), 'locations': locations}


class EvokedSensationsFrame(tk.Frame):
    # todo make this scrollable
    def __init__(self, master: tk.Widget, on_continue: Callable[[list[dict[str, Any]]], None], trial_number: int):
        """The Frame where the participant can add multiple evoked sensations and continue stimulation.
        :param master: The parent widget.
        :param on_continue: A function to call the participant presses continue.
        :param trial_number: The current trial number."""
        super().__init__(master,
                         highlightbackground='red', highlightthickness=2,
                         # relief='solid', borderwidth=2,
                         )
        self.on_continue = on_continue

        # The canvas is just here to enable scrolling and only contains the main_frame
        self.canvas = tk.Canvas(self,
                                highlightbackground='yellow', highlightthickness=2,
                                )
        # The main_frame contains all content except the scrollbar
        self.main_frame = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window((0, 0), window=self.main_frame, anchor='n')

        # link canvas and scrollbar
        scrollbar = tk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        # Make the entire canvas scrollable
        self.canvas.bind('<Configure>', self._on_canvas_resize)
        # resize the scroll region when the main_frame changes size (because sensations are added / removed)
        self.main_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)  # Add mousewheel scrolling

        self.canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header Frame
        header_frame = ttk.Frame(self.main_frame)
        header_frame.columnconfigure(0, weight=1)
        title = ttk.Label(header_frame, text='Evoked Sensations', font='bold')
        trial_number_label = ttk.Label(header_frame, text=f'Trial {trial_number}')
        title.grid(row=0, column=0, sticky="w")
        trial_number_label.grid(row=0, column=1, sticky="e")

        # Frame for all evoked sensations
        self.sensations_container = ttk.Frame(self.main_frame)
        self.no_sensations_label = ttk.Label(self.sensations_container,
                                             text="If you felt no sensations, please press continue.\nOtherwise, add a sensation.")
        self.sensations_frames = []
        self.add_sensation()

        # Add sensation button
        add_sensation_button = ttk.Button(self.main_frame, text='+ Add Sensation', command=self.add_sensation)

        # Continue button
        continue_button = ttk.Button(self.main_frame, text='▶️ Continue Stimulation',
                                     command=self.get_sensations_and_continue)

        header_frame.pack(fill='x', expand=True, padx=5, pady=5)
        self.sensations_container.pack(fill='x', expand=True, padx=5, pady=5)
        add_sensation_button.pack()
        continue_button.pack()

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        if sys.platform == 'darwin':  # mac
            delta = -1 * int(event.delta)
        else:  # windows
            delta = -1 * int(event.delta // 120)
        self.canvas.yview_scroll(delta, "units")

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

    def remove_sensation(self, query_sensation_frame):
        self.sensations_frames.remove(query_sensation_frame)
        self.update_sensations()
        query_sensation_frame.destroy()

    def add_sensation(self):
        self.sensations_frames.append(
            _SingleSensationFrame(self.sensations_container, len(self.sensations_frames) + 1, self.remove_sensation))
        self.update_sensations()

    # todo maybe delete this whole function and do it without regenerating everything!
    def update_sensations(self):
        """Call whenever a sensation is added or removed. Updates the QuerySensationFrames that are shown."""
        if len(self.sensations_frames) > 0:
            for row, sensation_frame in enumerate(self.sensations_frames):
                sensation_frame.title_label.config(text=f'Sensation {row + 1}')
                sensation_frame.grid(row=row, column=0, padx=5, pady=5)
                # sensation_frame.pack(fill='x', expand=True, padx=5, pady=5)
        else:
            self.no_sensations_label.grid(row=0, column=0, padx=5, pady=5)
            # self.no_sensations_label.pack(fill='x', expand=True, padx=5, pady=5)

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def get_sensations_and_continue(self):
        data = []
        for sensation in self.sensations_frames:
            data.append(sensation.get_sensation_data())
        self.on_continue(data)
