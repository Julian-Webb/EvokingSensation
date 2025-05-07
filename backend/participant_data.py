import logging
import json

from backend.settings import Settings


class ParticipantData:
    # todo delete?
    # CALIBRATION_DATA_FILE = 'calibration_data.json'
    # SENSATION_DATA_FILE = 'sensation_data.json'

    def __init__(self, ):
        """Handles the participant data, such as block and trial information, and inputted sensory data."""
        self.calibration_data = {}
        self.sensation_data = {}

    def update_calibration_data(self, iteration: int, amplitude_ma: float, intensity: str):
        self.calibration_data[iteration] = {'amplitude_ma': amplitude_ma, 'intensity': intensity}
        self.save_calibration_data()

    def update_sensation_data(self, overall_trial: int, sensations: list[dict]):
        """Update and save the sensation data for a trial
        :param overall_trial: The overall trial number
        :param sensations: A list of the different sensations for this trial"""
        self.sensation_data[overall_trial] = sensations
        self.save_sensation_data()

    def save_calibration_data(self):
        self._save_data(Settings().get_calibration_data_path(), self.calibration_data)

    def save_sensation_data(self):
        self._save_data(Settings().get_sensation_data_path(), self.sensation_data)

    @staticmethod
    def _save_data(path: str, data):
        try:
            with open(path, 'w') as file:
                json.dump(data, file)
            logging.info(f'Successfully saved data to {path}')
        except Exception as e:
            logging.error(f"Error saving dictionary to {path}: {str(e)}")
