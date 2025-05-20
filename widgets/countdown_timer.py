import tkinter as tk
import time


class CountdownTimer(tk.Frame):
    """A timer that counts down in seconds from a specified duration"""

    def __init__(self, master, duration_seconds: float, on_finish: callable):
        """
        A timer that counts down from a given duration.
        :param master: The parent widget
        :param duration_seconds: The duration of the timer in seconds
        :param on_finish: A function to call when the timer finishes
        """
        super().__init__(master)
        self.on_finish = on_finish
        self.duration_seconds = duration_seconds
        self.duration_label = tk.Label(self, text=self.format_time(duration_seconds) + ' minutes')
        self.duration_label.pack()
        self.start_time = None

    def start_timer(self):
        """Start the timer"""
        self.start_time = time.time()
        self._update_timer()

    def _update_timer(self):
        """Update the timer label"""
        elapsed_time = time.time() - self.start_time
        remaining_time = round(self.duration_seconds - elapsed_time)

        if remaining_time <= 0:
            self.duration_label.config(text='0:00 minutes')
            self.on_finish()
        else:
            self.duration_label.config(text=self.format_time(remaining_time) + ' minutes')
            # noinspection PyTypeChecker
            self.after(1000, self._update_timer)  # additional args are optional, but it shows a warning

    @staticmethod
    def format_time(dur_s: float) -> str:
        """Convert the duration in seconds to a formatted string with minutes and seconds"""
        minutes, seconds = divmod(dur_s, 60)
        return f"{int(minutes)}:{int(seconds):02}"


# example usage
if __name__ == '__main__':
    win = tk.Tk()
    timer = CountdownTimer(win, 70, lambda: print('finished'))
    timer.pack()
    tk.Button(win, text='Start', command=timer.start_timer).pack()
    win.mainloop()
