import tkinter as tk
from tkinter import ttk
from typing import Callable

from stimulator import Stimulator

_COUNTDOWN_DURATION = 3  # in seconds


class ParticipantWindow(tk.Toplevel):
    def __init__(self, master: tk.Tk, stimulator: Stimulator):
        super().__init__(master)
        self.stimulator = stimulator

        self.title('Participant View')
        self._initialize_window_position()

        self.current_frame = _CalibrationPhase(self, stimulator, self.start_sense_phase)
        self.current_frame.pack()

    def _initialize_window_position(self):
        """Positions the window on the right side of the screen."""
        # Get the screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Set window size
        window_width = 500
        window_height = 500

        # Calculate the position for the participant window
        # (placing it on the right side of the screen)
        x_position = int(screen_width / 2) - 400
        y_position = int((screen_height - window_height) / 2)

        # Set the window geometry to position it
        self.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    def start_sense_phase(self):
        print('Starting sensory response phase...')
        self.current_frame.destroy()
        self.current_frame = _SensoryResponsePhase(self, self.stimulator)
        self.current_frame.pack()


class _InitialFrame(ttk.Frame):
    def __init__(self, master: tk.Widget, title: str, start_stimulation: Callable):
        super().__init__(master)
        title_label = ttk.Label(self, text=title)
        title_label.pack()

        self.start_button = ttk.Button(self, text='▶️ Start Stimulation', command=start_stimulation)
        self.start_button.pack()


class _CountdownFrame(ttk.Frame):
    """A frame that shows a countdown before starting stimulation."""

    def __init__(self, master: tk.Widget, duration: int, on_finish: Callable):
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


class _StimulationFrame(ttk.Frame):
    def __init__(self, master: tk.Widget):
        super().__init__(master)

        title = ttk.Label(self, text='Stimulating...')
        title.pack()


class _CalibrationPhase(ttk.Frame):
    def __init__(self, master, stimulator: Stimulator, next_phase: Callable):
        super().__init__(master)
        self.stimulator = stimulator

        self.frame = None  # Current frame
        self.show_frame(_InitialFrame(self, 'Calibration Phase', self.start_countdown))

    def show_frame(self, frame: ttk.Frame):
        if self.frame is not None:
            self.frame.destroy()
        self.frame = frame
        frame.grid(row=0, column=0, sticky='nsew')

    def start_countdown(self):
        countdown_frame = _CountdownFrame(self, _COUNTDOWN_DURATION, self.stimulate)
        self.show_frame(countdown_frame)
        countdown_frame.start_countdown()

    def stimulate(self):
        self.show_frame(_StimulationFrame(self))
        self.after(2000, self.query_intensity)  # todo actual stimulation here

    def query_intensity(self):
        self.show_frame(self.InputIntensityFrame(self, on_continue=self.start_countdown))

    class InputIntensityFrame(ttk.Frame):
        def __init__(self, master: tk.Widget, on_continue: Callable):
            super().__init__(master)

            title = ttk.Label(self, text='Intensity Feedback')
            title.pack()

            # radio buttons for intensity
            intensity_label = ttk.Label(self, text='Sensation Intensity:')
            intensity_label.pack()

            continue_button = ttk.Button(self, text='▶️ Continue Stimulation', command=on_continue)
            continue_button.pack()

    class PhaseCompleted(ttk.Frame):
        def __init__(self, master, next_phase: Callable):
            super().__init__(master)
            title = ttk.Label(self, text='Calibration Phase Completed!')
            title.pack()

            continue_button = ttk.Button(self, text='Continue to sensory response phase', command=next_phase)
            continue_button.pack()


class _SensoryResponsePhase(ttk.Frame):
    def __init__(self, master, stimulator: Stimulator):
        super().__init__(master)
        self.stimulator = stimulator

        self.frame = None
        self.show_frame(_InitialFrame(self, 'Sensory Response Phase', self.start_countdown))

    def show_frame(self, frame: ttk.Frame):
        if self.frame is not None:
            self.frame.destroy()
        self.frame = frame
        frame.grid(row=0, column=0, sticky='nsew')

    def start_countdown(self):
        countdown_frame = _CountdownFrame(self, _COUNTDOWN_DURATION, self.stimulate)
        self.show_frame(countdown_frame)
        countdown_frame.start_countdown()

    def stimulate(self):
        self.show_frame(_StimulationFrame(self))
        self.after(2000, self.query_sensation)  # todo actual stimulation here

    def query_sensation(self):
        self.show_frame(self.QuerySensationFrame(self, on_continue=self.start_countdown))

    class QuerySensationFrame(ttk.Frame):
        def __init__(self, master: tk.Widget, on_continue: Callable):
            super().__init__(master)
            title = ttk.Label(self, text='Evoked Sensations')
            title.pack()

            # Field for sensations
            sensation_label = ttk.Label(self, text='Evoked Sensation:')
            sensation_label.pack()

            continue_button = ttk.Button(self, text='▶️ Continue Stimulation', command=on_continue)
            continue_button.pack()

    class BlockCompleted(ttk.Frame):
        def __init__(self, master, on_continue: Callable):
            super().__init__(master)
            # todo add logic for blocks; last block should show end of experiment
            title = ttk.Label(self, text='Block Completed! Time for a 5 minute break!')
            title.pack()

            continue_button = ttk.Button(self, text='Continue with next block', command=on_continue)
            continue_button.pack()
