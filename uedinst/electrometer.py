from contextlib import suppress
from math import ceil
from time import sleep
from warnings import warn

import numpy as np
from pyvisa import ResourceManager
from scipy.constants import elementary_charge

from . import GPIBBase, InstrumentException


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

        self.write("*RST;*CLS")

    def __exit__(self, *exc):
        error_codes = self.error_codes()
        if error_codes:
            warn("Error codes: {}".format(error_codes), UserWarning)
        with suppress(InstrumentException):
            self.write("*RST;*CLS")
        super().__exit__(*exc)

    @property
    def trigger_source(self):
        """ Trigger source, one of {'IMM', 'TLIN'} """
        return self.query("TRIG:SOUR?").strip("\n")

    @property
    def input_trigger_line(self):
        """ Input trigger line. Only valid for trigger mode 'TLIN' """
        return int(self.query("TRIG:TCON:ASYN:ILIN?").strip("\n"))

    @property
    def measurement_function(self):
        """ Measurement function, one of {'VOLT', 'CURR', 'RES', 'CHAR'} """
        # query is returned in the form '"VOLT:DC\n"'
        return self.query("CONF?").strip("\n").replace('"', "")

    def error_codes(self):
        """ 
        Return all errors in the error queue or None 
        
        Returns
        -------
        codes : iterable
            String error codes. If no error codes,
        """
        errors = self.query("SYST:ERR:CODE:ALL?").strip("\n")
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
        if trig not in {"IMM", "TLIN"}:
            raise ValueError(
                "Trigger source must be either IMM or TLIN, not {}".format(trig)
            )
        self.write("TRIG:SOUR {}".format(trig))
        self.write("TRIG:TCON:ASYN:ILIN {}".format(trig))

    def set_input_trigger_line(self, line):
        """
        Select input trigger line, from 1 to 6.

        Parameters
        ----------
        line : int between 1 and 6
            Trigger line to use.
        """
        if line not in (1, 2, 3, 4, 5, 6):
            raise ValueError(
                "Input trigger line must be between 1 and 6, not {}".format(line)
            )
        self.write("TRIG:TCON:ASYN:ILIN {}".format(str(line)))

    def set_measurement_function(self, func):
        """ Configure the electrometer to one of its measurement 
        functions: voltage, current, resistance or charge.

        Parameters
        ----------
        func : {'VOLT', 'CURR', 'RES', 'CHAR'}
            String representing the function to configure.
        """
        if func not in {"VOLT", "CURR", "RES", "CHAR"}:
            raise ValueError(
                'The only supported measurement functions are "VOLT", "CURR", \
                             "RES", or "CHAR", and {} is not one of them'
            )

        self.write("CONF:{}".format(func))
    
    def integrate(self, func, time, nplc=1):
        """
        Integrate the currently-chosen function for `time` amounts of time.

        Parameters
        ----------
        func : {'VOLT', 'CURR', 'RES', 'CHAR'}
            Measurement function
        time : float
            Integration time [s]
        nplc : float, optional
            Integration time in number of power-line cycles, i.e. factors of 60Hz. 
            Must be in the [0.01, 10] range (inclusive). Note that the default value 
            has the lowest measurement noise. `nplc < 1` drastically increases 
            measurement noise, while `1 < nplc < 10` is best.
        """
        if not (0.01 <= nplc <= 10):
            raise ValueError(f'nplc values must be within [0.01, 10], but got {nplc}.')
            
        # NPLC = number of power-line cycles
        # Reading time is actually empirically ~3 times 
        # higher than the integration time
        integration_time = nplc / 60
        one_reading_time = 3 * integration_time

        # For some reason, the "toggling" of zero-check is also the recommended way
        # to perform a zero-check.
        # Note that the recommended time to make a zero-check is **before** selecting a 
        # measurement function, for some reason.
        self.toggle_zero_check(True)

        self.set_measurement_function(func)
        self.write(f'{func}:NPLC {nplc}')

        # We acquire at least enough readings, and potentially a little more
        # This way, we may reject readings that were too late based on time-stamps
        # Its better to acquire too many readings than too little.
        num_readings = ceil(time / one_reading_time) + 2

        if num_readings > 2500:
            raise ValueError(f'Integration time of {time}s results in too many measurements.')

        to_arr = lambda iterable: np.fromiter(
            map(float, iterable), dtype=np.float, count=num_readings
        )

        self.write('ARM:SOUR IMM')
        self.write('ARM:COUN 1')
        self.write(f'TRIG:COUN {int(num_readings)}')

        self.write("TRAC:CLE")
        self.write("TRAC:TST:FORM ABS")
        self.write("FORM:ELEM READ,TIME")
        self.write(f"TRAC:POIN {int(num_readings)}")
        self.write(f"TRAC:FEED SENS1;FEED:CONT NEXT")

        # Launch measurement
        self.write(f"INIT")

        # Technically, we should wait_for_srq; however, this has proven to be very unreliable.
        sleep(1.1 * time)

        #npoints = int(self.query("TRAC:POIN:ACT?"))
        #print(f'Acquired {npoints} points')
        data = self.query("TRAC:DATA?").split(",")

        readings = to_arr(data[0::2])
        times    = to_arr(data[1::2])
        times   -= times.min()

        in_bounds = times <= time
        return np.trapz(y=readings[in_bounds], x=times[in_bounds])

    def toggle_display(self, toggle):
        """ Enable or disable electrometer display. Faster acquisition is possible if the display is
        turned off """
        b = "ON" if toggle else "OFF"
        self.write("DISP:ENAB {}".format(b))

    def toggle_autozero(self, toggle):
        """ Enable or disable electrometer autozeroing. Faster acquisition is possible
        if autozeroing is turned off """
        b = "ON" if toggle else "OFF"
        self.write("SYST:AZER {}".format(b))

    def toggle_zero_check(self, toggle):
        """ Enable or disable electrometer autozeroing. Faster acquisition is possible
        if autozeroing is turned off """
        b = "ON" if toggle else "OFF"
        self.write("SYST:ZCH {}".format(b))

class ExperimentElectrometer(Keithley6514):
    """
    Implementation of specific methods for experiments performed in the Siwick Research Group
    """

    def integrate_ecount_on_trigger(self, time, nplc=1):
        """
        This function arms the electrometer for a measurement of charge,
        triggered on TLINK 1, for `time` seconds, and returns the number
        of electrons measured.

        This function is specifically for experiments performed in the Siwick lab.

        Parameters
        ----------
        time : float
            Integration time [s]
        nplc : float, optional
            Integration time in number of power-line cycles, i.e. factors of 60Hz. 
            Must be in the [0.01, 10] range (inclusive). Note that the default value 
            has the lowest measurement noise. `nplc < 1` drastically increases 
            measurement noise, while `1 < nplc < 10` is best.

        Returns
        -------
        ecout : float
            Number of electrons detected.
        """
        self.write('SENS:CHAR:ADIS:STAT OFF')   # Turn Auto-discharge off
        self.write('SENS:CHAR:RANG:UPP 200E-9') # Most sensitive range of charge measurements

        self.set_trigger_source('TLIN')
        self.set_input_trigger_line(1)
        return self.integrate(func='CHAR', time=time, nplc=nplc)/elementary_charge
