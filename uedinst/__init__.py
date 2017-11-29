# -*- coding: utf-8 -*-
__author__ = 'Laurent P. René de Cotret'
__email__ = 'laurent.renedecotret@mail.mcgill.ca'
__license__ = 'BSD'
__version__ = '0.0.1'

from pyvisa.errors import VisaIOError
from serial import SerialException

# We have an exception
class InstrumentException(SerialException, VisaIOError):
    """ 
    Base exception for instrument-related errors. Abstraction 
    of pyvisa and pyserial's exceptions. 
    """
    pass

from .base import GPIBBase, SerialBase, MetaInstrument
from .electrometer import Keithley6514
from .powermeter import TekPSM4120
from .shutter import SC10Shutter