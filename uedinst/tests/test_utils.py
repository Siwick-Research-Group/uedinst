
import unittest
from .. import is_valid_IP

class TestIsValidIP(unittest.TestCase):

    TEST_ADDRESSES = {'255.255.255.255' : True,
                      '192.168.1.1'     : True,
                      '256.0.0.1'       : False, # max 255
                      '255.0.0'         : False}
    
    def test_addresses(self):
        """ Test known addresses """
        for key, val in self.TEST_ADDRESSES:
            self.assertEqual(is_valid_IP(key), val)

if __name__ == '__main__':
    unittest.main()