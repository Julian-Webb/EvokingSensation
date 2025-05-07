import ast
import logging
import random
from typing import Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np

@dataclass
class TrialInfo:
    """Contains overall_trial, block, trial, channels, and electrodes."""
    overall_trial: int
    block: int
    trial: int
    channels: list[int]
    electrodes: list[tuple[int]]

class StimulationOrder:
    def __init__(self):
        """This class takes care of creating and storing the order of stimulation regarding blocks, trials, channels,
        and electrode pairs."""
        # The nested list with the order. The levels are blocks > trials > channels.
        self.stim_order: Optional[pd.DataFrame] = None

        # The mapping of channels to electrodes. It should contain an entry for each channel (1-8) with a
        # tuple containing the electrodes (1-16)
        self.channel_electrode_map: Optional[dict] = None

        # The index for the overall trial (compared to the trial within a block)
        self.overall_trial: int = 1

        # example channel mapping TODO delete later
        self.channel_electrode_map = {1: (1, 2), 2: (3, 4), 3: (5, 6), 4: (7, 8), 5: (9, 10), 6: (11, 12), 7: (13, 14),
                                      8: (15, 16)}

    @classmethod
    def from_file(cls, path: str):
        """Create a StimulationOrder instance from an Excel (xlsx) file.
        :param path: File path"""
        instance = cls()
        # read the stimulation order (so)
        so = pd.read_excel(path, index_col='overall trial', dtype={'block': np.int64, 'trial': np.int64})

        # Convert str to list
        so['channels'] = so['channels'].apply(ast.literal_eval)
        so['electrodes'] = so['electrodes'].apply(ast.literal_eval)

        instance.stim_order = so
        return instance

    @classmethod
    def generate_new(cls, n_blocks: int = 4, n_trials_per_block: int = 8):
        """Create a StimulationOrder instance by generating a new stimulation order."""
        instance = cls()

        order = pd.DataFrame(columns=['block', 'trial', 'channels', 'electrodes'])
        order.index.name = 'overall trial'

        overall_trial = 1
        for block in range(1, n_blocks + 1):
            for trial in range(1, n_trials_per_block + 1):
                # Randomly select the number of channels in this trial. Favor lower numbers.
                n_channels_in_trial = random.choices(range(1, 9), weights=[8, 7, 6, 5, 4, 3, 2, 1])[0]
                channels = random.sample(range(1, 9), n_channels_in_trial)
                electrodes = [instance.channel_electrode_map[channel] for channel in channels]
                # Set the values
                order.loc[overall_trial] = {'block': block, 'trial': trial, 'channels': channels,
                                            'electrodes': electrodes}
                overall_trial += 1

        instance.stim_order = order

        return instance

    # for some reason it says that trial['block'] and trial['trial'] are invalid, so we turn off inspection
    # noinspection PyTypeChecker
    def current_trial(self):
        """Provides information on the current trial.
        :return: A dict with the block and trial numbers, channels, and electrodes for the current trial."""
        row = dict(self.stim_order.loc[self.overall_trial])
        # convert block and trial from np.int64 to int
        block = int(row['block'])
        trial = int(row['trial'])

        return TrialInfo(self.overall_trial, block, trial, row['channels'], row['electrodes'])

    def next_trial(self):
        """Advance to the next trial.
        :return: A dict with the block and trial numbers as well as the channels for the new trial if there is one, else None"""
        # todo handle end of experiment and block
        # Go to the next trial unless this is the last one.
        if self.overall_trial < len(self.stim_order):
            self.overall_trial += 1
            cur_trial = self.current_trial()
            logging.debug(f"New trial. Block: {cur_trial.block}, trial: {cur_trial.trial}")
            return cur_trial
        else:
            logging.debug("End of experiment.")
            return None

    def reset_block(self):
        """Reset to the first trial of the current block.
        :return: A dict with the block and trial numbers as well as the channels for the new trial."""
        # The index of the trial within the block is subtracted from the overall trial index to reset the block.
        trial_in_block = self.stim_order.loc[self.overall_trial, 'trial']
        self.overall_trial = self.overall_trial - trial_in_block + 1
        return self.current_trial()

    def save_as_excel(self, path: str):
        """Saves the stimulation order to .csv file."""
        # order_copy = self.stim_order.copy(deep=True) # todo use this?
        order_copy = self.stim_order

        # Alternate the background color of the blocks for readability
        style = self._color_blocks(order_copy)
        order_copy = style.data

        # Auto-adjust column width and save
        writer = pd.ExcelWriter(path, engine='xlsxwriter')
        sheet_name = 'StimulationOrder'
        style.to_excel(writer, sheet_name=sheet_name)
        worksheet = writer.sheets[sheet_name]
        for idx, col in enumerate(order_copy):
            series = order_copy[col]
            max_len = max((
                series.astype(str).map(len).max(),  # len of largest item
                len(str(series.name))  # len of column name/header
            )) + 0.1  # adding a little extra space
            worksheet.set_column(idx + 1, idx + 1, max_len)  # set column width
        writer.close()


    @staticmethod
    def _color_blocks(dataframe):
        """Sets an alternating color for the blocks."""

        def color_alternate(x):
            color1 = '#E5FFE5'  # light green
            color2 = '#E5E5FF'  # light blue
            return ['background-color: {}'.format(color1 if x['block'] % 2 == 0 else color2) for _ in range(len(x))]

        return dataframe.style.apply(color_alternate, axis=1)


if __name__ == '__main__':
    stim_order = StimulationOrder.generate_new()
    stim_order.save_as_excel("C:\\Users\\julia\\PycharmProjects\\EvokingSensation\\data\\test_stim_order1.xlsx")
