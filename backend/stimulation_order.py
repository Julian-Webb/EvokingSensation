import ast
import random
import pandas as pd
import numpy as np


class StimulationOrder:
    def __init__(self):
        """This class takes care of creating and storing the order of stimulation regarding blocks, trials, channels,
        and electrode pairs."""
        # The nested list with the order. The levels are blocks > trials > channels.
        self.stim_order = None

        # The mapping of channels to electrodes. It should contain an entry for each channel (1-8) with a
        # tuple containing the electrodes (1-16)
        self.channel_electrode_map = None

        # The index for the overall trial (compared to the trial within a block)
        self.overall_trial = 0

        # example channel mapping TODO delete later
        self.channel_electrode_map = {1: (1, 2), 2: (3, 4), 3: (5, 6), 4: (7, 8), 5: (9, 10), 6: (11, 12), 7: (13, 14),
                                      8: (15, 16)}

    @classmethod
    def from_file(cls, path: str):
        """Create a StimulationOrder instance from an xlsx file.
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
    def generate_new(cls):
        """Create a StimulationOrder instance by generating a new stimulation order."""
        # todo delete or implement
        pass

    @staticmethod
    def generate_order():
        # TODO implement properly
        n_blocks = 4
        n_trials = 8

        blocks = []
        for block in range(n_blocks):
            trials = []
            for trial in range(n_trials):
                n_channels_in_trial = random.randint(1, 8)
                channels = random.sample(range(1, 9), n_channels_in_trial)
                trials.append(channels)
            blocks.append(trials)

        # convert to dataframe

        return blocks

    def current_trial(self):
        """Provides information on the current trial.
        :return: A dict with the block and trial numbers, channels, and electrodes for the current trial."""
        trial = dict(self.stim_order.iloc[self.overall_trial])
        # convert block and trial from np.int64 to int
        trial['block'] = int(trial['block'])
        trial['trial'] = int(trial['trial'])
        return trial

    def next_trial(self):
        """Advance to the next trial.
        :return: A dict with the block and trial numbers as well as the channels for the new trial."""
        # todo handle end of experiment and block
        self.overall_trial += 1
        return self.current_trial()

    def reset_block(self):
        """Reset to the first trial of the current block.
        :return: A dict with the block and trial numbers as well as the channels for the new trial."""
        # The index of the trial within the block is subtracted from the overall trial index to reset the block.
        trial_in_block = self.stim_order.loc[self.overall_trial, 'trial']
        self.overall_trial -= trial_in_block
        return self.current_trial()

    def save_as_excel(self, path: str):
        """Saves the stimulation order to .csv file.
        :return: The dataframe that was generated based on the stimulation order and saved."""
        # todo adjust for stim_order as dataframe in class

        # Turn the order into a dataframe
        data = []

        for block_idx, trials in enumerate(self.stim_order):
            for trial_idx, channels in enumerate(trials):
                # Get the correct electrodes for each channel based on the mapping
                electrodes = [self.channel_electrode_map[i] for i in channels]
                data.append({
                    'block': block_idx,
                    'trial': trial_idx,
                    'channels': channels,
                    'electrodes': electrodes,
                })
        df = pd.DataFrame(data)
        df.index.name = 'overall trial'

        # Alternate the background color of the blocks for readability
        style = self._color_blocks(df)
        df = style.data

        # Auto-adjust column width and save
        writer = pd.ExcelWriter(path, engine='xlsxwriter')
        sheet_name = 'StimulationOrder'
        style.to_excel(writer, sheet_name=sheet_name)
        worksheet = writer.sheets[sheet_name]
        for idx, col in enumerate(df):
            series = df[col]
            max_len = max((
                series.astype(str).map(len).max(),  # len of largest item
                len(str(series.name))  # len of column name/header
            )) + 0.1  # adding a little extra space
            worksheet.set_column(idx + 1, idx + 1, max_len)  # set column width
        writer.close()

        return df

    @staticmethod
    def _color_blocks(dataframe):
        """Sets an alternating color for the blocks."""

        def color_alternate(x):
            color1 = '#E5FFE5'  # light green
            color2 = '#E5E5FF'  # light blue
            return ['background-color: {}'.format(color1 if x['block'] % 2 == 0 else color2) for _ in range(len(x))]

        return dataframe.style.apply(color_alternate, axis=1)

