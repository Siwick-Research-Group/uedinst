
import unittest
from contextlib import suppress
from random import randint, seed, choice
seed(23)

from .. import SC10Shutter, InstrumentException

HAS_SC10 = False
with suppress(InstrumentException):
    SC10Shutter('COM11')        # probe shutter
    HAS_SC10 = True

@unittest.skipIf(not HAS_SC10, 'No SC10Shutter is connected')
class TestSC10Shutter(unittest.TestCase):

    def setUp(self):
        self.shutter = SC10Shutter('COM11')
    
    def tearDown(self):
        self.shutter.close()
    
    def test_enable(self):
        """ Test that shutter enabling works """
        for enable in {True, False}:
            self.shutter.enable(enable)
            self.assertEqual(enable, self.shutter.enabled)
    
    def test_operating_mode(self):
        """ Test that setting the operating mode and retrieving works """
        op_mode = choice(list(self.shutter.OperatingModes))
        self.shutter.set_operating_mode(op_mode)
        self.assertEqual(op_mode, self.shutter.operating_mode)
    
    def test_trigger_mode(self):
        """ Test that setting the trigger mode and retrieving it works """
        trig_mode = choice(list(self.shutter.TriggerModes))
        self.shutter.set_trigger_mode(trig_mode)
        self.assertEqual(trig_mode, self.shutter.trigger_mode)
    
    def test_open_time(self):
        """ Test that setting the open time to a random number is working correctly """
        open_time = randint(1, 100)
        self.shutter.set_open_time(open_time)
        self.assertEqual(open_time, self.shutter.shutter_open_time)
    
    def test_repeat_count(self):
        """ Test that the repeat count can be set and retrieved """
        repeat_count = randint(1, 100)
        self.shutter.set_repeat_count(repeat_count)
        self.assertEqual(repeat_count, self.shutter.repeat_count)
        

if __name__ == '__main__':
    unittest.main()