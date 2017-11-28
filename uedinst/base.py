
from pyvisa import ResourceManager
from pyvisa.resources import GPIBInstrument

class GPIBBase:
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