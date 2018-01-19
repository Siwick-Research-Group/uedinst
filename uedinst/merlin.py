
from contextlib import AbstractContextManager
from .merlin_drivers import MERLIN_connection

class Merlin(AbstractContextManager):

    """
    Wrapper around the MERLIN_connection API.

    This API can be used as a context manager:
    >>> with MerlinAPI(...) as merlin:
    ...     pass

    Parameters
    ----------
    hostname : str, optional
    
    ipaddress : str, optional
        (Local) IP address of the Merlin Quad server.
    """
    def __init__(self, hostname = 'diamrd', ipaddress = '000'):
        self._cmd_api  = MERLIN_connection(hostname, ipaddress, channel = 'cmd')
        #self._data_api = MERLIN_connection(hostname, ipaddress, channel = 'data')
    
    def __exit__(self, *args, **kwargs):
        self._cmd_api.sock.close()
        #self._data_api.sock.close()
        super().__exit__(*args, **kwargs)
    
    @property
    def sensor_temperature(self):
        """ Immediate sensor temperature in celsius. """
        return self._cmd_api.getFloatNumericVariable('TEMPERATURE')
    
    @property
    def hv_bias(self):
        """ High-voltage sensor bias """
        return self._cmd_api.getFloatNumericVariable('HVBIAS')

    @property
    def acquisition_time(self):
        """ Image acquisition time """
        return self._cmd_api.getFloatNumericVariable('ACQUISITIONTIME')

    @property
    def numframes(self):
        """ Number of images to acquire on next start """
        return self._cmd_api.getIntNumericVariable('NUMFRAMESTOACQUIRE')

    def trigger_start(self):
        """ Trigger an acquisition. Acquisition will start at the next
        trigger pulse. """
        self._cmd_api.setValue('TRIGGERSTART', 1)
    
    def trigger_stop(self):
        """ Stop an acquisition on the next trigger """
        self._cmd_api.setValue('TRIGGERSTOP', 0)
    

