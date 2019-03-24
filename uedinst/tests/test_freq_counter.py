import unittest
from contextlib import suppress

from .. import RacalDana1991, InstrumentException

HAS_FREQ_COUNTER = False
with suppress(InstrumentException):
    RacalDana1991("GPIB::17")
    HAS_FREQ_COUNTER = True


@unittest.skipIf(not HAS_FREQ_COUNTER, "Racal-Dana 1991 instrument not connected.")
class TestRacalDana1991(unittest.TestCase):
    def test_frequency(self):
        with RacalDana1991("GPIB::17") as freq_counter:
            freq = freq_counter.frequency()


if __name__ == "__main__":
    unittest.main()
