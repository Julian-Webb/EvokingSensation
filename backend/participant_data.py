import logging
import json
from datetime import datetime
from tkinter import messagebox
from backend.settings import Settings
from backend.stimulation_order import TrialInfo


class ParticipantData:
    def __init__(self, ):
        """Handles the participant data, such as block and trial information, and inputted sensory data."""
        self.calibration_data = []
        self.sensation_data = {}

    def update_calibration_data(self, amplitude_ma: float, intensity: str):
        self.calibration_data.append({'timestamp': datetime.now().isoformat(), 'amplitude_ma': amplitude_ma,
                                      'intensity': intensity})
        self.save_calibration_data()

    def update_sensation_data(self, trial_info: TrialInfo, sensations: list[dict]):
        """Update and save the sensation data for a trial.
        :param trial_info: The information for this trial.
        :param sensations: A list of the different sensations for this trial"""
        self.sensation_data[trial_info.overall_trial] = {'timestamp': datetime.now().isoformat(),
                                                         'sensations': sensations,
                                                         # Use the correct attributes in trial_info
                                                         **{key: getattr(trial_info, key) for key in
                                                            ['block', 'trial', 'channels', 'electrodes']}}
        self.save_sensation_data()

    def save_calibration_data(self):
        self._save_data(Settings().get_calibration_data_path(), self.calibration_data)

    def save_sensation_data(self):
        self._save_data(Settings().get_sensation_data_path(), self.sensation_data)

    @staticmethod
    def _save_data(path: str, data):
        """Save the data to the given path and retry until it has been successfully saved"""
        while True:
            try:
                with open(path, 'w') as file:
                    json.dump(data, file)
                logging.info(f'Successfully saved data to {path}')
                break
            except Exception as e:
                logging.error(f"Error saving dictionary to {path}: {str(e)}")
                messagebox.showerror(
                    'Error storing data',
                    'There was an error saving the participant data. '
                    'Please fix the issue (e.g., close the file or resolve permissions) and try again.'
                )

