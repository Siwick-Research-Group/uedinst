
import unittest
from contextlib import suppress

from .. import Keithley6514, InstrumentException

HAS_KEITHLEY = False
with suppress(InstrumentException):
    Keithley6514('GPIB::15')
    HAS_KEITHLEY = True

@unittest.skipIf(not HAS_KEITHLEY, 'Keithley 6514 instrument not connected')
class TestKeithley6514(unittest.TestCase):

    def setUp(self):
        self.electrometer = Keithley6514('GPIB::15')
    
    def test_acquire_buffered(self):
        """ Test that ``acquire_buffered()`` works as expected. """
        self.electrometer.set_measurement_function('CHAR')
        self.electrometer.set_trigger_source('IMM')
        data = self.electrometer.acquire_buffered(num = 10, timeout = 20000)
        self.assertTupleEqual((10, 2), data.shape)
    
    def test_repeated_acquire_buffered(self):
        """ In the past, multiple ``acquire_buffered`` calls would fail """
        self.electrometer.set_measurement_function('CHAR')
        self.electrometer.set_trigger_source('IMM')
        for _ in range(3):
            data = self.electrometer.acquire_buffered(num = 2, timeout = 20000)
            self.assertTupleEqual((2, 2), data.shape)
    
    def test_measurement_function(self):
        """ Test that setting the measurement function is propagated 
        correctly """
        for meas_func in {'VOLT', 'CURR', 'RES', 'CHAR'}:
            self.electrometer.set_measurement_function(meas_func)
            # We cannot test equality since property may return 'VOLT:DC' for example
            self.assertIn(meas_func, self.electrometer.measurement_function)

if __name__ == '__main__':
    unittest.main()
