import time

def waiting_dots_animation(wait_time: float):
    """Shows some dots while waiting for a process to finish.
    It's necessary to have 3 dots already printed before calling this function.
    :param wait_time: time to wait in seconds."""
    step_wait_time = wait_time / 4

    time.sleep(step_wait_time)
    print('\b\b\b', end='', flush=True)
    time.sleep(step_wait_time)
    print('.', end='', flush=True)
    time.sleep(step_wait_time)
    print('.', end='', flush=True)
    time.sleep(step_wait_time)
    print('.', end='', flush=True)

def windows_dpi_awareness():
    """Set the DPI awareness for Windows to avoid blurry text and images."""
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass