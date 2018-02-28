
import unittest
from contextlib import suppress

from .. import ITC503, InstrumentException

HAS_ITC503 = False
with suppress(InstrumentException):
    ITC503()
    HAS_ITC503 = True

@unittest.skipIf(not HAS_ITC503, 'ITC503 temperature controller not connected.')
class TestITC503(unittest.TestCase):
    
    def setUp(self):
        self.temp_controller = ITC503()

    def tearDown(self):
        self.temp_controller._instrument.close()
        del self.temp_controller

    def test_state(self):
        for state in ITC503.ControlState:

            self.temp_controller.set_control(state)
            self.assertEqual(state, self.temp_controller.control_state)
        
        self.temp_controller.set_control(ITC503.ControlState.RemoteUnlocked)

if __name__ == '__main__':
    unittest.main()