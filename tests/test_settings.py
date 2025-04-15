import unittest
from settings import Settings
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
        s.amplitude.set('5')
        self.assertEqual(s.amplitude.get(), '5', "amplitude_mA should be '5'")

    def test_period_from_frequency(self):
        root = tk.Tk()
        s = Settings()
        freq = 5.0
        s.frequency.set(str(freq))
        period_ms = (1 / freq) * 1000

        period_returned = float(s.period.get())
        self.assertEqual(period_returned, period_ms,
                         f"period_ms should be {period_ms} ms based on frequency {freq} Hz but is {period_returned}")

    def test_channel(self):
        root = tk.Tk()
        s = Settings()
        channel_int = 5
        channel_adjusted = channel_int - 1
        s.channel.set(str(channel_int))
        self.assertEqual(s.channel_adjusted, channel_adjusted, f"channel_adjusted should be {channel_adjusted}")

    def test_set_channel_adjusted(self):
        # test whether it's possible to set the adjusted channel (it shouldn't be)
        root = tk.Tk()
        s = Settings()
        with self.assertRaises(AttributeError):
            s.channel_adjusted = 5

# if __name__ == '__main__':
#     unittest.main()
#     print("All tests passed.")
