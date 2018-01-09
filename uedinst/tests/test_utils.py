
import unittest
from time import sleep

from .. import is_valid_IP, timeout


class TestIsValidIP(unittest.TestCase):

    TEST_ADDRESSES = {'255.255.255.255' : True,
                      '192.168.1.1'     : True,
                      '256.0.0.1'       : False, # max 255
                      '255.0.0'         : True}
    
    def test_addresses(self):
        """ Test known addresses """
        for key, val in self.TEST_ADDRESSES.items():
            with self.subTest('{} should be {}'.format(key, val)):
                self.assertEqual(is_valid_IP(key), val)

class TestTimeoutContextManager(unittest.TestCase):

    def test_timeout_not_triggered(self):
        """ Test the timeout context without raising """
        with timeout(1, RuntimeError):
            pass
    
    def test_timeout_other_exception(self):
        """ Test that exceptions from within the context (unrelated
        to timeout) are properly propagated """
        with self.assertRaises(RuntimeError):
            with timeout(1, ValueError):
                raise RuntimeError

    def test_timeout_expired(self):
        """ Test that an exception is raised if timeout expires """
        with self.assertRaises(RuntimeError):
            with timeout(0.1, RuntimeError):
                while True:
                    sleep(0.0001)
                    pass
    
    def test_value_guards(self):
        """ Test that ValueError is raised if invalid error messages
        or timeout are passed to ``timeout`` """
        with self.subTest('Error message not string'):
            with self.assertRaises(ValueError):
                with timeout(0.1, RuntimeError, None):
                    pass
        
        with self.subTest('Timeout below zero'):
            with self.assertRaises(ValueError):
                with timeout(-1, RuntimeError):
                    pass

if __name__ == '__main__':
    unittest.main()
