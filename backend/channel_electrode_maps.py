# The mapping of channels to electrodes.
# It's a dict containing map IDs, and channel-electrode-maps
# Each channel-electrode-map contains an entry for each channel (1-8) with a list containing a tuple of electrodes (1-16)

CHANNEL_ELECTRODE_MAPS = {
    "horizontal": {1: (1, 2), 2: (3, 4), 3: (5, 6), 4: (7, 8), 5: (9, 10), 6: (11, 12), 7: (13, 14), 8: (15, 16)},
    "vertical": {1: (1, 5), 2: (2, 6), 3: (3, 7), 4: (4, 8), 5: (9, 13), 6: (10, 14), 7: (11, 15), 8: (12, 16)}
}
