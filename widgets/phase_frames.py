# The different frames that are iterated through in a phase
import tkinter as tk
from tkinter import ttk
from typing import Callable


class TextAndButtonFrame(tk.Frame):
    def __init__(self, master, title_text: str, button_text: str, command: Callable):
        super().__init__(master)
        title = ttk.Label(self, text=title_text, font='bold')
        title.pack()

        continue_button = ttk.Button(self, text=button_text, command=command)
        continue_button.pack()


class CountdownFrame(tk.Frame):
    def __init__(self, master: tk.Widget, duration: int, on_finish: Callable):
        """The Frame that shows a countdown before starting stimulation."""
        super().__init__(master)
        self.duration_var = tk.IntVar(self, value=duration)
        self.on_finish = on_finish

        self.duration_label = ttk.Label(self, textvariable=self.duration_var)
        self.duration_label.pack()

    def start_countdown(self):
        self.after(1000, self._countdown, [])  # empty list for unused *args

    def _countdown(self, *_):
        """Used to start the countdown and is recursively called to update the countdown and terminate."""
        current = self.duration_var.get()
        current -= 1
        if current > 0:
            self.duration_var.set(current)
            self.after(1000, self._countdown, [])  # empty list for unused *args
        else:
            self.on_finish()


class StimulationFrame(tk.Frame):
    def __init__(self, master: tk.Widget):
        """The Frame to show when stimulation is ongoing"""
        super().__init__(master)

        title = ttk.Label(self, text=_('Stimulating...'))
        title.pack()


class InputIntensityFrame(tk.Frame):
    # noinspection PyUnreachableCode
    if False: # Just so gettext realizes that these strings need to be translated
        _('Nothing')
        _('Very weak')
        _('Weak')
        _('Moderate')
        _('Strong')
        _('Very strong')
        _('Painful')

    INTENSITY_OPTIONS = ['Nothing', 'Very weak', 'Weak', 'Moderate', 'Strong', 'Very strong', 'Painful']

    def __init__(self, master: tk.Widget, on_continue: Callable[[str], None]):
        """The Frame to ask the participant what intensity they feel after stimulating during the calibration phase."""
        super().__init__(master)

        self.intensity_var = tk.StringVar(self)

        title = ttk.Label(self, text=_('Intensity Feedback'), font='bold')
        title.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # radio buttons for intensity
        intensity_label = ttk.Label(self, text=_('Sensation Intensity:'))
        intensity_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        for idx, intensity in enumerate(self.INTENSITY_OPTIONS):
            # The command enables continuing only when a button is selected.
            button = ttk.Radiobutton(self, variable=self.intensity_var, text=_(intensity),  value=intensity,
                                     command=lambda: self.continue_button.config(state='normal'))
            button.grid(row=1, column=idx + 1, padx=5, pady=5)

        self.continue_button = ttk.Button(self, text=_('Continue Stimulation'), state='disabled',
                                          command=lambda: on_continue(self.intensity_var.get()))
        self.continue_button.grid(row=2, column=0, padx=5, pady=5)


class ExperimentCompleted(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        title = ttk.Label(self, text=_('Experiment Completed!\nThank you for participating!'))
        title.pack()
