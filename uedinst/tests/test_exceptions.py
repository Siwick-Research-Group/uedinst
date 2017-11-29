
from contextlib import suppress
import unittest

from serial import SerialException
from pyvisa.errors import VisaIOError

from .. import InstrumentException

class TestException(unittest.TestCase):

    def test_subclasses(self):
        """ Test that catching Pyvisa and serial errors also catches InstrumentException """
        
        with self.subTest('PyVisa VisaIOError'):
            with suppress(VisaIOError):
                raise InstrumentException
        
        with self.subTest('PySerial SerialException'):
            with suppress(SerialException):
                raise InstrumentException