import logging
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Any

from backend.settings import Settings
from backend.stimulation_order import StimulationOrder
from backend.stimulator import Stimulator, StimulatorError

# _COUNTDOWN_DURATION = 3 # in seconds
_COUNTDOWN_DURATION = 1  # in seconds # todo back to 3


class ParticipantWindow(tk.Toplevel):
    def __init__(self, master: tk.Tk, stimulator: Stimulator, stim_order: StimulationOrder):
        super().__init__(master)
        self.stimulator = stimulator
        self.stim_order = stim_order

        self.title('Participant View')
        self._initialize_window_position()

        # disabled closing the window
        self.protocol("WM_DELETE_WINDOW",
                      lambda: messagebox.showinfo("Not closable",
                                                  "This window must be closed in the experimenter view"))

        self.current_frame = _CalibrationPhase(self, stimulator, self.start_sense_phase)
        self.current_frame.grid(row=0, column=0, sticky='nsew')

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # self.start_sense_phase()  # todo delete after testing
        # self.current_frame.query_sensation()  # todo delete after testing

    def _initialize_window_position(self):
        """Positions the window on the right side of the screen."""
        # Get the screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Set window size
        window_width = 1000
        window_height = 1000

        # Calculate the position for the participant window
        # (placing it on the right side of the screen)
        x_position = int(screen_width / 2) - 400
        # y_position = int((screen_height - window_height) / 2)
        y_position = 0

        # Set the window geometry to position it
        self.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    def start_sense_phase(self):
        logging.info('--- Sensory Response Phase ---')
        self.current_frame.destroy()
        self.current_frame = _SensoryResponsePhase(self, self.stimulator, self.stim_order)
        self.current_frame.grid(row=0, column=0, sticky='nsew')


class _InitialFrame(ttk.Frame):
    def __init__(self, master: tk.Widget, title: str, start_stimulation: Callable):
        super().__init__(master)
        title_label = ttk.Label(self, text=title)
        title_label.pack()

        self.start_button = ttk.Button(self, text='▶️ Start Stimulation', command=start_stimulation)
        self.start_button.pack()


class _CountdownFrame(ttk.Frame):
    """The Frame that shows a countdown before starting stimulation."""

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
    """The Frame to show when stimulation is ongoing"""

    def __init__(self, master: tk.Widget):
        super().__init__(master)

        title = ttk.Label(self, text='Stimulating...')
        title.pack()


class _CalibrationPhase(ttk.Frame):

    def __init__(self, master, stimulator: Stimulator, on_phase_over: Callable):
        super().__init__(master)
        self.stimulator = stimulator
        self.on_phase_over = on_phase_over

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
        s = Settings()
        # update the pulse configuration
        self.stimulator.rectangular_pulse(s.channel.get(), s.amplitude.get(), s.phase_duration.get(),
                                          s.interphase_interval.get(), s.period_numeric())
        self.stimulator.stimulate_ml(s.stim_duration.get(), self.query_intensity, self.on_stimulation_error)
        self.show_frame(_StimulationFrame(self))

    def on_stimulation_error(self, channel: int):
        self.stimulator.stop_stimulation()
        messagebox.showerror(title="Stimulator Error.",
                             message=f"The stimulator has reported an error on channel {channel}. Stimulation stopped.")
        raise StimulatorError('The stimulator signaled an error.')
        # todo decide what the program should do now. It currently just get's stuck in the StimulationFrame

    def adjust_amplitude(self, intensity: str):
        """Adjust the amplitude based on the intensity selected by the participant.
        :param intensity: The intensity selected by the participant."""
        # TODO this function doesn't continue yet if the amplitude is at its minimum/maximum but the participant doesn't
        #  feel a very strong sensation. How should this be handled?

        if intensity == 'Nothing':
            increment_ma = 3.0  # increment in milliampere
        elif intensity == 'Very weak':
            increment_ma = 2.0
        elif intensity == 'Weak':
            increment_ma = 1.5
        elif intensity == 'Moderate':
            increment_ma = 1.0
        elif intensity == 'Strong':
            increment_ma = 0.5
        elif intensity == 'Very strong':
            increment_ma = 0.0
        elif intensity == 'Painful':
            increment_ma = -1.0
        else:
            raise ValueError(
                'intensity should be in ["Nothing", "Very weak", "Weak", "Moderate", "Strong", "Very strong", "Painful"]')

        if increment_ma != 0.0:
            new_amplitude = Settings().amplitude.get() + increment_ma
            # make sure it's in range
            minimum, maximum = Settings().PARAMETER_OPTIONS['amplitude']['range']
            new_amplitude = float(np.clip(new_amplitude, minimum, maximum))
            if new_amplitude in [minimum, maximum]:
                logging.info(
                    f'Amplitude has reached its {"minimum" if new_amplitude == minimum else "maximum"} of {new_amplitude} mA.')
            else:
                logging.info(f'Increasing amplitude by {increment_ma} mA to {new_amplitude} mA')
            Settings().amplitude.set(new_amplitude)
            self.start_countdown()
        else:
            # We've reached our target intensity and the calibration phase is over.
            self.show_frame(self.PhaseCompleted(self, self.on_phase_over))

    def query_intensity(self):
        self.show_frame(self.InputIntensityFrame(self, on_continue=self.adjust_amplitude))

    class InputIntensityFrame(ttk.Frame):
        INTENSITY_OPTIONS = ['Nothing', 'Very weak', 'Weak', 'Moderate', 'Strong', 'Very strong', 'Painful']

        def __init__(self, master: tk.Widget, on_continue: Callable[[str], None]):
            super().__init__(master)

            self.intensity_var = tk.StringVar(self)

            title = ttk.Label(self, text='Intensity Feedback', font='bold')
            title.grid(row=0, column=0, padx=5, pady=5, sticky="w")

            # radio buttons for intensity
            intensity_label = ttk.Label(self, text='Sensation Intensity:')
            intensity_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

            for idx, intensity in enumerate(self.INTENSITY_OPTIONS):
                # The command enables continuing only when a button is selected.
                button = ttk.Radiobutton(self, text=intensity, variable=self.intensity_var, value=intensity,
                                         command=lambda: self.continue_button.config(state='normal'))
                button.grid(row=1, column=idx + 1, padx=5, pady=5)

            self.continue_button = ttk.Button(self, text='▶️ Continue Stimulation', state='disabled',
                                              command=lambda: on_continue(self.intensity_var.get()))
            self.continue_button.grid(row=2, column=0, padx=5, pady=5)

    class PhaseCompleted(ttk.Frame):
        def __init__(self, master, next_phase: Callable):
            super().__init__(master)
            title = ttk.Label(self, text='Calibration Phase Completed!')
            title.pack()

            continue_button = ttk.Button(self, text='Continue to sensory response phase', command=next_phase)
            continue_button.pack()


class _SensoryResponsePhase(ttk.Frame):
    def __init__(self, master, stimulator: Stimulator, stim_order: StimulationOrder):
        super().__init__(master)
        self.stimulator = stimulator
        self.stim_order = stim_order

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
        s = Settings()
        # update the pulse configuration
        for channel in self.stim_order.current_trial()['channels']:
            self.stimulator.rectangular_pulse(channel, s.amplitude.get(), s.phase_duration.get(),
                                              s.interphase_interval.get(), s.period_numeric())
        self.stimulator.stimulate_ml(s.stim_duration.get(), self.query_sensation, self.on_stimulation_error)
        self.show_frame(_StimulationFrame(self))

    def on_stimulation_error(self, channel: int):
        self.stimulator.stop_stimulation()
        messagebox.showerror(title="Stimulator Error.",
                             message=f"The stimulator has reported an error on channel {channel}. Stimulation stopped.")
        raise StimulatorError('The stimulator signaled an error.')
        # todo decide what the program should do now.

    def query_sensation(self):
        # todo adjust trial number
        self.show_frame(self.EvokedSensationsFrame(self, on_continue=self.on_continue_after_querying,
                                                   trial_number=self.stim_order.current_trial()['trial']))

    def on_continue_after_querying(self, sensations: list[dict[str, Any]]):
        """What to do after querying is finished and the participant presses continue stimulation."""
        # Save sensation data
        print(sensations)

        # Continue
        old_block = self.stim_order.current_trial()['block']
        new_trial_info = self.stim_order.next_trial()
        if new_trial_info is None:
            # End of Experiment
            self.on_end_of_experiment()
        elif old_block != new_trial_info['block']:
            # End of block
            self.on_end_of_block()
        else:
            # Regular trial
            self.start_countdown()

    def on_end_of_block(self):
        self.show_frame(self.BlockCompleted(self, self.start_countdown))

    def on_end_of_experiment(self):
        self.show_frame(self.ExperimentCompleted(self))

    class EvokedSensationsFrame(ttk.Frame):
        # todo make this scrollable
        def __init__(self, master: tk.Widget, on_continue: Callable[[list[dict[str, Any]]], None], trial_number: int):
            """The Frame where the participant can add multiple evoked sensations and continue stimulation.
            :param master: The parent widget.
            :param on_continue: A function to call the participant presses continue.
            :param trial_number: The current trial number."""
            super().__init__(master)
            self.on_continue = on_continue

            # Header Frame
            header_frame = ttk.Frame(self)
            header_frame.columnconfigure(0, weight=1)
            title = ttk.Label(header_frame, text='Evoked Sensations', font='bold')
            trial_number_label = ttk.Label(header_frame, text=f'Trial {trial_number}')
            title.grid(row=0, column=0, sticky="w")
            trial_number_label.grid(row=0, column=1, sticky="e")

            # Frame for all evoked sensations
            self.sensations_container = ttk.Frame(self)
            self.no_sensations_label = ttk.Label(self.sensations_container,
                                                 text="If you felt no sensations, please press continue.\nOtherwise, add a sensation.")
            self.sensations_frames = []
            self.add_sensation()

            # Add sensation button
            add_sensation_button = ttk.Button(self, text='+ Add Sensation', command=self.add_sensation)

            # Continue button
            continue_button = ttk.Button(self, text='▶️ Continue Stimulation', command=self.get_sensations_and_continue)

            header_frame.pack(fill='x', expand=True, padx=5, pady=5)
            self.sensations_container.pack(fill='x', expand=True, padx=5, pady=5)
            add_sensation_button.pack()
            continue_button.pack()

        def remove_sensation(self, query_sensation_frame):
            self.sensations_frames.remove(query_sensation_frame)
            self.update_sensations()
            query_sensation_frame.destroy()

        def add_sensation(self):
            self.sensations_frames.append(
                self.SingleSensationFrame(self.sensations_container, len(self.sensations_frames) + 1,
                                          self.remove_sensation))
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

        def get_sensations_and_continue(self):
            data = []
            for sensation in self.sensations_frames:
                data.append(sensation.get_sensation_data())
            self.on_continue(data)

        class SingleSensationFrame(ttk.Frame):
            SENSATION_TYPES = ['Touch', 'Pulse', 'Tingling', 'Vibration', 'Cramp', 'Pain', 'Heat', 'Cold', 'Other']
            INTENSITY_OPTIONS = [i for i in range(1, 11)]
            LOCATIONS = ['D1', 'D2', 'D3', 'D4', 'S1', 'S2', 'S3', 'S4', 'S5', 'calf', 'shin']

            def __init__(self, master, sensation_number: int, on_remove):
                """A Frame which lets the participant input information for a single sensation.
                :param master: The parent widget.
                :param sensation_number: The number of the sensation.
                :param on_remove: A function to call when the sensation is removed."""
                super().__init__(master, relief='solid', borderwidth=2)

                # Initialize tkinter vars for inputs
                self.type_var = tk.StringVar(self)
                self.intensity_var = tk.IntVar(self)
                self.location_vars = {location: tk.IntVar(self, value=0) for location in self.LOCATIONS}

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
                                    ).grid(row=0, column=idx+1, padx=5, pady=(5, 0))
                # labels for intensity
                ttk.Label(intensity_frame, text='Mild', anchor='center').grid(row=1, column=1, columnspan=3, sticky='ew')
                ttk.Label(intensity_frame, text='Moderate', anchor='center').grid(row=1, column=4, columnspan=4, sticky='ew')
                ttk.Label(intensity_frame, text='Strong', anchor='center').grid(row=1, column=8, columnspan=3, sticky='ew')

                # location frame
                location_frame = ttk.Frame(self)
                location_label = ttk.Label(location_frame, text='Location:')
                location_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

                # make checkboxes for each location
                for idx, location in enumerate(self.LOCATIONS):
                    ttk.Checkbutton(location_frame, text=location, variable=self.location_vars[location],
                                    ).grid(row=0, column=idx + 1, padx=5, pady=5, sticky="w")


                # Put all the frames together
                for frame in [header_frame, type_frame, intensity_frame, location_frame]:
                    frame.pack(fill='x', expand=True, padx=5, pady=5)

            def get_sensation_data(self):
                """Access the data the participant has input for this sensation.
                :returns: A dict with the entries 'type', 'intensity', and 'locations'."""
                locations = [loc for loc in self.LOCATIONS if self.location_vars[loc].get() == 1]
                return {'type': self.type_var.get(), 'intensity': self.intensity_var.get(), 'locations': locations}


    class BlockCompleted(ttk.Frame):
        def __init__(self, master, on_continue: Callable[[], None]):
            super().__init__(master)
            # todo add logic for blocks; last block should show end of experiment
            title = ttk.Label(self, text='Block Completed! Time for a 5 minute break!')
            title.pack()

            continue_button = ttk.Button(self, text='Continue with next block', command=on_continue)
            continue_button.pack()

    class ExperimentCompleted(ttk.Frame):
        def __init__(self, master):
            super().__init__(master)
            title = ttk.Label(self, text='Experiment Completed!\nThank you for participating!')
            title.pack()
