import tkinter
import logging
from experimenter_window import ExperimenterWindow
from stimulator import Stimulator
from utils import windows_dpi_awareness
from settings import Settings

if __name__ == '__main__':
    # --- Internal Settings ---
    windows_dpi_awareness()
    logging.basicConfig(level=logging.DEBUG)
    # -------------------------

    stimulator = Stimulator()
    experimenter_window = ExperimenterWindow(stimulator)

    experimenter_window.mainloop()
