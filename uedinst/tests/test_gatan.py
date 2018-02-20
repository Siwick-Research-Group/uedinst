
import unittest
from contextlib import suppress
import numpy as np

from .. import GatanUltrascan895, InstrumentException

CAMERA_AVAILABLE = False
with suppress(InstrumentException):
    camera = GatanUltrascan895()
    CAMERA_AVAILABLE = True
    camera.close()

@unittest.skipIf(not CAMERA_AVAILABLE, 'Gatan Ultrascan 895 camera not connected/available.')
class TestGatanUltrascan895(unittest.TestCase):

    def setUp(self):
        self.camera = GatanUltrascan895()
    
    def tearDown(self):
        self.camera.close()

    def test_image(self):
        """ Test that images from the GatanUltrascan895 are of expected shape and datatype """
        im = self.camera.acquire_image(0.5)

        self.assertEqual(im.dtype, np.int16)
        self.assertTupleEqual(im.shape, (2048, 2048))
        
if __name__ == '__main__':
    unittest.main()