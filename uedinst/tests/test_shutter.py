
import unittest
from contextlib import suppress

from .. import SC10Shutter, InstrumentException

HAS_SC10 = False
with suppress(InstrumentException):
    SC10Shutter('COM11')        # probe shutter
    HAS_SC10 = True

@unittest.skipIf(not HAS_SC10, 'No SC10Shutter is connected')
class TestSC10Shutter(unittest.TestCase):

    def setUp(self):
        self.shutter = SC10Shutter('COM11')
        self.shutter.readall()  # clear buffer 
    
    def tearDown(self):
        self.shutter.close()
    
    def test_enable(self):
        """ Test that shutter enabling works """
        for enable in {True, False}:
            self.shutter.enable(enable)
            self.assertEqual(enable, self.shutter.enabled)
    
    def test_operating_mode(self):
        """ Test that setting the operating mode and retrieving works """
        for op_mode in self.shutter._op_modes:
            self.shutter.set_operating_mode(op_mode)
            self.assertEqual(op_mode, self.shutter.operating_mode)
    
    def test_trigger_move(self):
        """ Test that setting the trigger mode and retrieving it works """
        for trig_mode in self.shutter._trigger_modes:
            self.shutter.set_trigger_mode(trig_mode)
            self.assertEqual(trig_mode, self.shutter.trigger_mode)
        

if __name__ == '__main__':
    unittest.main()