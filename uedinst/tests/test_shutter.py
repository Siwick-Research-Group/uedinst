
import unittest
from contextlib import suppress

from .. import SC10Shutter, InstrumentException

HAS_SC10 = False
with suppress(InstrumentException):
    SC10Shutter('COM11')        # probe shutter
    HAS_SC10 = True

@unittest.skipIf(not HAS_SC10, 'No SC10Shutter is connected')
class TestSC10Shutter(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()