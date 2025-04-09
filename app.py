import tkinter
from utils import windows_dpi_awareness
from settings import Settings
import logging


if __name__ == '__main__':
    # --- Internal Settings ---
    windows_dpi_awareness()
    logging.basicConfig(level=logging.DEBUG)
    # -------------------------


    root = tkinter.Tk()
    root.title('Stimulation Sensation Experiment')

    Settings.amplitude_mA


    root.mainloop()

