import unittest
from settings import Settings


class TestSettings(unittest.TestCase):
    def test_singleton(self):
        s1 = Settings()
        s2 = Settings()
        self.assertIs(s1, s2, "Settings should be a singleton")

    def test_change_property(self):
        s = Settings()
        s.amplitude_mA = 5
        self.assertEqual(s.amplitude_mA, 5, "amplitude_mA should be 5")

    def test_period_from_frequency(self):
        s = Settings()
        freq = 5
        s.frequency_hz = freq
        period_ms = (1 / freq) * 1000

        self.assertEqual(s.period_ms, period_ms, f"period_ms should be {period_ms} ms based on frequency {freq} Hz")

    def test_channel(self):
        s = Settings()
        channel_input = 5
        s.channel_input = channel_input
        self.assertEqual(s.channel_adjusted, channel_input - 1, f"channel_adjusted should be {channel_input - 1}")

    def test_set_channel_adjusted(self):
        s = Settings()
        with self.assertRaises(AttributeError):
            s.channel_adjusted = 5

# if __name__ == '__main__':
#     unittest.main()
#     print("All tests passed.")
