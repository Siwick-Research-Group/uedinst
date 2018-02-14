
from . import GPIBBase

class RacalDana1991(GPIBBase):
    """
    Interface to Racal-Dana 1991 Frequency Counter. 
    
    This class supports context management:

    .. code::

        with RacalDana1991('GPIB::17') as freq_counter:
            pass

    Parameters
    ----------
    addr : str
        Instrument address, e.g. 'GPIB::15'
    kwargs
        Keyword arguments are passed to the pyvisa.ResourceManager.open_resource
        method.
    """

    def __init__(self, addr, **kwargs):
        kwargs['read_termination'] = '\r'
        super().__init__(addr, **kwargs)

        self.write('FA')
        self.write('T0')
    
    def frequency(self):
        """
        Return the frequency value.

        Returns
        -------
        frequency : float
        """
        raw = self.read()
        return float(raw.replace('FA', ''))