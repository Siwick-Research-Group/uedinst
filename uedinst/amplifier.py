
from abc import ABC, abstractmethod
from contextlib import suppress
from warnings import warn

import serial

from . import GPIBBase, SerialBase, TCPBase, InstrumentException


class OphirRFAmplifierMixin(ABC):
    """
    Base class for an OPHIR RF amplifier.

    """
    @abstractmethod
    def __init__(self, *args, **kwargs): pass
    
    @abstractmethod
    def write(self, *args, **kwargs): pass

    @abstractmethod
    def read(self, *args, **kwargs): pass
    
    @abstractmethod
    def query(self, *args, **kwargs): pass
    
    @property
    def forward_power(self):
        """ Amplifier forward power """
        return float(self.query('FWD_PWR?')[0:5])
    
    @property
    def reverse_power(self):
        """ Amplifier reverse power """
        return float(self.query('REV_PWR?')[0:5])
    
    @property
    def alc_level(self):
        """ Automatic level control setpoint """
        return float(self.query('ALC_LEVEL?')[0:5])
    
    def set_standby(self, enable):
        """
        Enable/disable standby.

        Parameters
        ----------
        enable : bool
        """
        message = 'STANDBY' if enable else 'ONLINE'
        self.write(message)

class OphirRFAmplifierGPIB(GPIBBase, OphirRFAmplifierMixin):
    """
    GPIB interface to an Ophir RF amplifier.

    Parameters
    ----------
    port : int
        GPIB port
    """
    def __init__(self, port, *args, **kwargs):
        super().__init__(addr = 'GPIB::{:d}'.format(port))

class OphirRFAmplifierSerial(SerialBase, OphirRFAmplifierMixin):
    """
    GPIB interface to an Ophir RF amplifier.

    Parameters
    ----------
    port : int
        GPIB port
    """

    def __init__(self, port, *args, **kwargs):
		kwargs.update({'port':     port,
					   'baudrate': 9600,
                       'bytesize': serial.EIGHTBITS,
                       'parity'  : serial.PARITY_NONE,
                       'stopbits': serial.STOPBITS_ONE,
					   'timeout':  1.0,
                       })
        super().__init__(**kwargs)

class OphirRFAmplifierTCP(TCPBase, OphirRFAmplifierMixin):
    """
    TCP/IP interface to an Ophir RF amplifier.

    Parameters
    ----------
    ip : str
        IP address, e.g. '127.0.0.1'
    port : int
        IP port
    """
    def __init__(self, ip, port, **kwargs):
        super().__init__(addr = ip, port = port, **kwargs)
    
    def write(self, message):
        return self.socket.write(message)
    
    def read(self):
        return self.socket.recv()
    
    def query(self, message):
        self.write(message)
        return self.read()
