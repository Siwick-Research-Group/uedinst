
from contextlib import AbstractContextManager, suppress

import numpy as np
from pyvisa import VisaIOError, ResourceManager

from warnings import warn
from . import GPIBBase

class Keithley6514(GPIBBase):
    """
    Interface to Keithley 6514 Electrometer. 
    
    This class supports context management:

    .. code::

        with Keithley6514('GPIB::15') as electrometer:
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
        self.write('*RST;*CLS')
        self.write('FORM:ELEM READ, TIME')
    
    def __exit__(self, *exc):
        error_codes = self.error_codes()
        if error_codes:
            warn('Error codes: {}'.format(error_codes), UserWarning)
        with suppress(VisaIOError):
            self.write('*RST;*CLS')
        super().__exit__(*exc)

    @property
    def trigger_source(self):
        """ Trigger source, one of {'IMM', 'TLIN'} """
        return self.query('TRIG:SOUR?').strip('\n')

    @property
    def input_trigger_line(self):
        """ Input trigger line. Only valid for trigger mode 'TLIN' """
        return int(self.query('TRIG:TCON:ASYN:ILIN?').strip('\n'))

    @property
    def measurement_function(self):
        """ Measurement function, one of {'VOLT', 'CURR', 'RES', 'CHAR'} """
        return self.query('CONF?').strip('\n')
    
    def error_codes(self):
        """ 
        Return all errors in the error queue or None 
        
        Returns
        -------
        codes : iterable
            String error codes. If no error codes,
        """
        errors = self.query('SYST:ERR:CODE:ALL?').strip('\n')
        self.write('SYST:CLE')   # clear error queue
        try:
            int(errors) == 0
        except ValueError:
            return errors
        else:
            return None
    
    def set_trigger_source(self, trig):
        """ 
        Set the trigger source to be either immediate (IMM) or trigger link (TLIN) 
        
        Parameters
        ----------
        trig : {'IMM', 'TLIN'}
            Trigger source.
        """
        if trig not in {'IMM', 'TLIN'}:
            raise ValueError('Trigger source must be either IMM or TLIN, not {}'.format(trig))
        self.write('TRIG:SOUR {}'.format(trig))
    
    def set_input_trigger_line(self, line):
        """
        Select input trigger line, from 1 to 6.

        Parameters
        ----------
        line : int between 1 and 6
            Trigger line to use.
        """
        if line not in (1,2,3,4,5,6):
            raise ValueError('Input trigger line must be between 1 and 6, not {}'.format(line))
        self.write('TRIG:TCON:ASYN:ILIN {}'.format(str(line)))

    def set_measurement_function(self, func):
        """ Configure the electrometer to one of its measurement 
        functions: voltage, current, resistance or charge.

        Parameters
        ----------
        func : {'VOLT', 'CURR', 'RES', 'CHAR'}
            String representing the function to configure.
        """
        if func not in {'VOLT', 'CURR', 'RES', 'CHAR'}:
            raise ValueError('The only supported measurement functions are "VOLT", "CURR", \
                             "RES", or "CHAR", and {} is not one of them')
        
        self.write('CONF:{}'.format(func))
    
    def acquire_buffered(self, num, timeout = None):
        """
        Acquire ``num`` buffered readings. 

        Parameters
        ----------
        num : int
            Number of measurements to store in buffer. Maximum of 2500 values.
        timeout : int or None, optional
            Timeout of the operation in milliseconds. 
            If None (default), timeout is disabled
        
        Returns
        -------
        arr : `~numpy.ndarray`, shape (N,2)
            Time and readings arrays. The first column are the
            time-stamps in seconds, while the second column are the readings.
        
        Raises
        ------
        ValueError: if ``num`` is too large (> 2500)
        InstrumentException: if buffer didn't fill up before timeout expired

        Notes
        -----
        For best performance, the display should be toggled off.
        """
        num = int(num)
        if num > 2500:
            raise ValueError('Cannot store more than 2500 readings in the buffer.')

        self.write('TRIG:COUN {}'.format(num))

        self.write('*SRE 9')                # Lookout for buffer full
        self.write('STAT:PRES')             # Reset all event lines
        self.write('STAT:MEAS:ENAB 512')

        self.write('TRAC:CLE')                  # Clear buffer
        self.write('TRAC:POIN {}'.format(num))  # Set number of buffer points
        self.write('TRAC:FEED SENS1')           # Store raw measurements
        self.write('TRAC:FEED:CONT NEXT')       # Start buffered acquisition
        self.write('INIT')                      # Bring electrometer out of idle state

        # Prepare some things while data acquisition
        arr = np.empty(shape = (num, 2), dtype = np.float)
        to_arr = lambda iterable: np.fromiter(map(float, iterable), 
                                              dtype = np.float, count = num)

        # Wait until buffer is full        
        self.wait_for_srq(timeout)

        data = self.query('TRAC:DATA?').split(',')
        arr[:,0] = to_arr(data[1::2])   # time
        arr[:,1] = to_arr(data[0::2])   # readings
        return arr
    
    def toggle_display(self, toggle):
        """ Enable or disable electrometer display. Faster acquisition is possible if the display is
        turned off """
        b = 'ON' if toggle else 'OFF'
        self.write('DISP:ENAB {}'.format(b))
    
    def toggle_autozero(self, toggle):
        """ Enable or disable electrometer autozeroing. Faster acquisition is possible
        if autozeroing is turned off """
        b = 'ON' if toggle else 'OFF'
        self.write('SYST:AZER {}'.format(b))
    
    def toggle_zero_check(self, toggle):
        """ Enable or disable electrometer autozeroing. Faster acquisition is possible
        if autozeroing is turned off """
        b = 'ON' if toggle else 'OFF'
        self.write('SYST:ZCH {}'.format(b))