import logging
from tkinter import messagebox
from typing import Any, override

import numpy as np

from backend.participant_data import ParticipantData
from backend.stimulation_order import StimulationOrder
from backend.stimulator import Stimulator
from .evoked_sensations_frame import EvokedSensationsFrame
from .phase_frames import *


class _BasePhase(tk.Frame):
    def __init__(self, master, stimulator: Stimulator, participant_data: ParticipantData):
        """To be used as a parent class for all phases."""
        super().__init__(master)
        self.stimulator, self.participant_data = stimulator, participant_data
        self.frame = None  # Current frame

    def show_frame(self, frame: tk.Frame):
        if self.frame is not None:
            self.frame.destroy()
        self.frame = frame
        frame.grid(row=0, column=0, sticky='nsew')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def start_countdown(self):
        if Settings.COUNTDOWN_DURATION > 0:
            countdown_frame = CountdownFrame(self, Settings.COUNTDOWN_DURATION, self.stimulate)
            self.show_frame(countdown_frame)
            countdown_frame.start_countdown()
        else:
            # This case is just for development
            self.stimulate()


    def stimulate(self):
        raise NotImplementedError

    def on_stimulation_error(self, channel: int):
        messagebox.showerror(title="Stimulator Error.",
                             message=f"The stimulator has reported an error on channel {channel}. Stimulation stopped.")
        # todo LATER add German translation
        self.show_frame(TextAndButtonFrame(self, title_text=_('Stimulator Error'), body_text=_(
            'The stimulator has encountered an error.\nPlease ask the experimenter to fix any issues.\nThen, the trial will be repeated.'),
                                           button_text='▶ ' + _('Continue Stimulation'), command=self.start_countdown))

    def query_after_stimulation(self):
        raise NotImplementedError

    def on_continue_after_querying(self, *args, **kwargs):
        raise NotImplementedError

    def on_end_of_phase(self):
        raise NotImplementedError


class CalibrationPhase(_BasePhase):

    def __init__(self, master, stimulator: Stimulator, participant_data: ParticipantData, on_phase_over: Callable):
        """The Frame for the calibration phase where the participant can adjust the amplitude of the stimulation."""
        super().__init__(master, stimulator, participant_data)
        self.on_end_of_phase = on_phase_over
        self.show_frame(
            TextAndButtonFrame(self, title_text=_('Calibration Phase'), button_text='▶ ' + _('Start Stimulation'),
                               command=self.start_countdown))

    @override
    def stimulate(self):
        s = Settings()
        # update the pulse configuration
        self.stimulator.rectangular_pulse(s.channel.get(), s.get_stimulation_parameters())
        self.stimulator.stimulate_ml(s.stim_duration.get(), self.query_after_stimulation, self.on_stimulation_error)
        self.show_frame(StimulationFrame(self))

    @override
    def query_after_stimulation(self):
        self.show_frame(InputIntensityFrame(self, on_continue=self.on_continue_after_querying))

    def on_continue_after_querying(self, intensity: str):
        """Save the stimulation amplitude and reported intensity and adjust the amplitude based on the intensity selected by the participant.
        :param intensity: The intensity selected by the participant."""
        # Save stimulation parameters
        self.participant_data.update_calibration_data(Settings().amplitude.get(), intensity)

        # Adjust the amplitude
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
            self.show_frame(TextAndButtonFrame(self, _('Calibration Phase Completed!'),
                                               _('Continue to sensory response phase'), self.on_end_of_phase))


class SensoryPhase(_BasePhase):
    def __init__(self, master, stimulator: Stimulator, participant_data: ParticipantData, stim_order: StimulationOrder):
        """The Frame for the sensory phase"""
        super().__init__(master, stimulator, participant_data)
        self.stim_order = stim_order
        self.show_frame(TextAndButtonFrame(self, _('Sensory Response Phase'),
                                           '▶ ' + _('Start Stimulation'), self.start_countdown))

    @override
    def stimulate(self):
        s = Settings()
        # update the pulse configuration
        for channel in self.stim_order.current_trial().channels:
            self.stimulator.rectangular_pulse(channel, s.get_stimulation_parameters())
        self.stimulator.stimulate_ml(s.stim_duration.get(), self.query_after_stimulation, self.on_stimulation_error)
        self.show_frame(StimulationFrame(self))

    @override
    def query_after_stimulation(self):
        self.show_frame(EvokedSensationsFrame(self, on_continue=self.on_continue_after_querying,
                                              trial_number=self.stim_order.current_trial().trial,
                                              trials_in_block=self.stim_order.n_trials_in_current_block()))

    @override
    def on_continue_after_querying(self, sensations: list[dict[str, Any]]):
        """What to do after querying is finished and the participant presses continue stimulation.
        :param sensations: A dict of the sensations the participant entered."""
        # Save sensation data
        old_trial_info = self.stim_order.current_trial()
        self.participant_data.update_sensation_data(old_trial_info, sensations)

        # Continue
        new_trial_info = self.stim_order.next_trial()
        if new_trial_info is None:
            # End of Experiment
            self.on_end_of_phase()
        elif old_trial_info.block != new_trial_info.block:
            # End of block
            # The completed block number is passed because it will show "Block n completed"
            self.on_end_of_block(old_trial_info.block, self.stim_order.n_blocks())
        else:
            # Regular trial
            self.start_countdown()

    def on_end_of_block(self, completed_block_number: int, n_blocks: int):
        self.show_frame(EndOfBlockFrame(self, completed_block_number, n_blocks, self.start_countdown))

    @override
    def on_end_of_phase(self):
        self.show_frame(ExperimentCompletedFrame(self))
