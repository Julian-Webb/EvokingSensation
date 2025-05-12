import logging
import tkinter as tk
from tkinter import messagebox

from backend.participant_data import ParticipantData
from backend.stimulation_order import StimulationOrder
from backend.stimulator import Stimulator
from .phases import CalibrationPhase, SensoryPhase


class ParticipantWindow(tk.Toplevel):
    def __init__(self, master: tk.Tk, stimulator: Stimulator, stim_order: StimulationOrder,
                 participant_data: ParticipantData):
        super().__init__(master)
        self.stimulator, self.stim_order, self.participant_data = stimulator, stim_order, participant_data

        self.title('Participant View')
        self._initialize_window_position()

        # disabled closing the window
        self.protocol("WM_DELETE_WINDOW",
                      lambda: messagebox.showinfo("Not closable",
                                                  "This window must be closed in the experimenter view"))

        self.current_frame = CalibrationPhase(self, stimulator, self.participant_data, self.start_sense_phase, )
        self.current_frame.grid(row=0, column=0, sticky='nsew')

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # self.start_sense_phase()  # todo delete after testing
        # self.current_frame.query_after_stimulation()  # todo delete after testing

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
        logging.info('--- Sensory Phase ---')
        self.current_frame.destroy()
        self.current_frame = SensoryPhase(self, self.stimulator, self.participant_data, self.stim_order)
        self.current_frame.grid(row=0, column=0, sticky='nsew')
