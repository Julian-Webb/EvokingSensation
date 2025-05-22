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

        self.title(_('Participant View'))

        self.state('zoomed')  # Make the window fullscreen
        self.minsize(1200, 900)

        # disabled closing the window
        self.protocol("WM_DELETE_WINDOW",
                      lambda: messagebox.showinfo(_("Not closable"),
                                                  _("This window must be closed in the experimenter view")))

        self.current_frame = CalibrationPhase(self, stimulator, self.participant_data, self.start_sense_phase, )
        self.current_frame.grid(row=0, column=0, sticky='nsew')

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # self.start_sense_phase()  # todo ON_LAUNCH delete after testing
        # self.current_frame.query_after_stimulation()  # todo ON_LAUNCH delete after testing


    def start_sense_phase(self):
        logging.info('--- Sensory Phase ---')
        self.current_frame.destroy()
        self.current_frame = SensoryPhase(self, self.stimulator, self.participant_data, self.stim_order)
        self.current_frame.grid(row=0, column=0, sticky='nsew')
