from contextlib import suppress
from math import ceil
from time import sleep
from warnings import warn

import numpy as np
from pyvisa import ResourceManager
from scipy.constants import elementary_charge

from . import GPIBBase, InstrumentException


class TekDMM4040(GPIBBase):
    """
    Interface to Tektronix DMM4040 Multimeter. 
    
    This class supports context management:

    .. code::

        with TekDMM4040('GPIB::15') as multimeter:
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
        super().__init__(addr, **kwargs)
        self.write("*RST;*CLS")

    def __exit__(self, *exc):
        error_codes = self.error_codes()
        if error_codes is not None:
            warn(f"Error codes: {error_codes}", UserWarning)
        with suppress(InstrumentException):
            self.write("*RST;*CLS")
        super().__exit__(*exc)

    def error_codes(self):
        """ 
        Return all errors in the error queue or None 
        
        Returns
        -------
        codes : iterable
            String error codes. If no error codes,
        """
        errors = self.query("SYST:ERR?").strip("\n")
        if errors[0:2] == "+0":
            return None
        return errors

    def voltage(self):
        """ Measure the instantaneous DC voltage """
        return float(self.query("MEAS:DC?"))
