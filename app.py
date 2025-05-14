import logging
from widgets.experimenter_window import ExperimenterWindow
from utils import windows_dpi_awareness

if __name__ == '__main__':
    # --- Internal Settings ---
    windows_dpi_awareness()
    logging.basicConfig(level=logging.DEBUG)
    # -------------------------

    experimenter_window = ExperimenterWindow()

    experimenter_window.mainloop()
