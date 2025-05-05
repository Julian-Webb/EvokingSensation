import unittest
from backend.settings import Settings
import tkinter as tk


class TestSettings(unittest.TestCase):

    def test_singleton(self):
        root = tk.Tk()
        s1 = Settings()
        s2 = Settings()
        self.assertIs(s1, s2, "Settings should be a singleton")

    def test_change_property(self):
        root = tk.Tk()
        s = Settings()
        s.amplitude.set(5)
        self.assertEqual(s.amplitude.get(), 5, "amplitude_mA should be 5")

    def test_period_from_frequency(self):
        root = tk.Tk()
        s = Settings()
        freq = 5.0
        s.frequency.set(freq)
        period_ms = (1 / freq) * 1000

        period_returned = float(s.period_string_var.get())
        self.assertEqual(period_returned, period_ms,
                         f"period_ms should be {period_ms} ms based on frequency {freq} Hz but is {period_returned}")



# if __name__ == '__main__':
#     unittest.main()
#     print("All tests passed.")
