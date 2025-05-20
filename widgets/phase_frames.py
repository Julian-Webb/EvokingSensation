# The different frames that are iterated through in a phase
import tkinter as tk
from tkinter import ttk
from typing import Callable

from backend.settings import Settings
from widgets.countdown_timer import CountdownTimer


class TextAndButtonFrame(tk.Frame):
    def __init__(self, master, title_text: str, button_text: str, command: Callable, body_text: str = ''):
        """A simple Frame with a title, optional body text, and a button.
        :param master: The parent widget.
        :param title_text: The title text.
        :param button_text: The button text.
        :param command: The command to execute when the button is pressed.
        :param body_text: Optional body text."""
        super().__init__(master)
        ttk.Label(self, text=title_text, style='Heading1.TLabel').pack(pady=(40, 20))

        if body_text != '':
            ttk.Label(self, text=body_text).pack(pady=20)

        ttk.Button(self, text=button_text, padding=(20, 20), command=command).pack(padx=20, pady=20)


class CountdownFrame(tk.Frame):
    def __init__(self, master: tk.Widget, duration: int, on_finish: Callable):
        """The Frame that shows a countdown before starting stimulation."""
        super().__init__(master)
        self.duration_var = tk.IntVar(self, value=duration)
        self.on_finish = on_finish

        self.duration_label = ttk.Label(self, textvariable=self.duration_var, style='Heading2.TLabel')
        self.duration_label.pack(pady=(100, 0))

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

        title = ttk.Label(self, text=_('Stimulating...'), style='Heading2.TLabel')
        title.pack(pady=(100, 0))


class InputIntensityFrame(tk.Frame):
    # noinspection PyUnreachableCode
    if False:  # Just so gettext realizes that these strings need to be translated
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

        title = ttk.Label(self, text=_('Intensity Feedback'), style='Heading1.TLabel')

        # radio buttons for intensity
        intensity_frame = ttk.Frame(self)
        intensity_label = ttk.Label(intensity_frame, text=_('Sensation Intensity:'), style='Bold.TLabel')
        intensity_label.grid(row=0, column=0, padx=(0, 5), pady=10, sticky="w")

        for idx, intensity in enumerate(self.INTENSITY_OPTIONS):
            # The command enables continuing only when a button is selected.
            button = ttk.Radiobutton(intensity_frame, variable=self.intensity_var, text=_(intensity), value=intensity,
                                     command=lambda: self.continue_button.config(state='normal'))
            button.grid(row=0, column=1 + idx, padx=5, pady=5, sticky='w')

        self.continue_button = ttk.Button(self, text='▶ ' + _('Continue Stimulation'), state='disabled', padding=20,
                                          command=lambda: on_continue(self.intensity_var.get()))
        # Arrange objects
        title.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        intensity_frame.grid(row=1, column=0, padx=20, pady=20, sticky="w")
        self.continue_button.grid(row=2, column=0, padx=(20, 5), pady=(20, 0), sticky='w')


class EndOfBlockFrame(tk.Frame):
    def __init__(self, master, completed_block_number: int, n_blocks: int, on_continue: Callable[[], None], ):
        super().__init__(master)
        # title
        ttk.Label(self, text=_('Block {} of {} Completed').format(completed_block_number, n_blocks),
                  style='Heading1.TLabel').pack(pady=(40, 20))

        # instructions
        # todo localization
        ttk.Label(self, text=_('Time for a break')).pack(pady=20)

        # timer and continue button
        continue_button = ttk.Button(self, text='▶ ' + _('Continue stimulation'), state='disabled', padding=(20, 20),
                                     command=on_continue)
        timer = CountdownTimer(self, Settings().BREAK_AFTER_BLOCK_DURATION_SEC,
                               lambda: continue_button.config(state='normal'))
        timer.pack(pady=20)
        continue_button.pack(padx=20, pady=20)
        timer.start_timer()


class ExperimentCompletedFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        title = ttk.Label(self, text=_('Experiment Complete'), style='Heading1.TLabel')
        body = ttk.Label(self, text=_('Thank you for participating!\n\nThis window can be safely closed now.'))
        title.pack(pady=10)
        body.pack(pady=10)
