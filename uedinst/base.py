
from abc import ABCMeta

from pyvisa import ResourceManager
from pyvisa.errors import VisaIOError
from pyvisa.resources import GPIBInstrument
from serial import Serial, SerialException

from . import InstrumentException


def general_exception(func, *wrapped_exc):
    def new_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (VisaIOError, SerialException):
            raise InstrumentException
    return new_func

class MetaInstrument(ABCMeta):
    """
    Metaclass that wraps all methods so that VisaIOError and SerialException
    are raised as InstrumentException.
    """

    def __init__(self, clsname, bases, clsdict):
        super().__init__(clsname, bases, clsdict)

        for name, value in clsdict.items():
            if not callable(value): 
                continue
            else:
                setattr(self, name, general_exception(value))

class GPIBBase(metaclass = MetaInstrument):
    """ 
    Base class for GPIB instruments. It wraps PyVisa's ResourceManager with open resources.
    ``GPIBBase`` also supports context managemenent (``with`` statement).
    
    Parameters
    ----------
    addr : str
        Instrument address, e.g. 'GPIB::15'.
    kwargs
        Keyword arguments are passed to the pyvisa.ResourceManager.open_resource method.
    """

    def __init__(self, addr, **kwargs):
        self._rm = ResourceManager()
        self._instrument = self._rm.open_resource(resource_name = addr, **kwargs)

    def __enter__(self):
        return self
    
    def __exit__(self, *exc):
        self._instrument.close()
        self._rm.close()

    def write(self, *args, **kwargs):
        return self._instrument.write(*args, **kwargs)
    
    def read(self, *args, **kwargs):
        return self._instrument.read(*args, **kwargs)
    
    def query(self, *args, **kwargs):
        return self._instrument.query(*args, **kwargs)

    write.__doc__ = GPIBInstrument.write.__doc__
    read.__doc__  = GPIBInstrument.read.__doc__
    query.__doc__ = GPIBInstrument.query.__doc__

    def wait_for_srq(self, timeout = 25000):
        """
        Wait for a serial request (SRQ) or the timeout to expire.

        Parameters
        ----------
        timeout : int or None, optional
            The maximum waiting time in milliseconds. 
            None means waiting forever if necessary.
        
        Raises
        ------
        pyvisa.error.VisaIOError: if timeout has expired
        """
        return self._instrument.wait_for_srq(timeout)

class SerialBase(Serial, metaclass = MetaInstrument):
    pass
