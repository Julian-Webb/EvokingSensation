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

    experimenter_window = ExperimenterWindow()

    experimenter_window.mainloop()
