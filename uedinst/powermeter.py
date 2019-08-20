import sys
from ctypes import CDLL, c_double, c_long

# Iff DLL is not available, LB_API2 will be None
if sys.platform == "win32":
    dll_path = (
        "C:\\Program Files\\Tektronix\\Tektronix Power Sensor Applications\\LB_API2.dll"
    )
    try:
        LB_API2 = CDLL(dll_path)
    except:
        LB_API2 = None
else:
    LB_API2 = None

# Error checking
# Most (all?) functions in the LB_API2 DLL return an int with
# error being anything below or equal to zero
def runtime_error_if_less_than(threshold):
    """ Returns an errcheck function """

    def errcheck(result, func, arguments):
        if result < threshold:
            raise RuntimeError("{} failed with arguments {}".format(func, arguments))

    return errcheck


# LB_API2 might not be on this computer
if LB_API2 is not None:
    LB_API2.LB_GetAddress_Idx.errcheck = runtime_error_if_less_than(1)
    LB_API2.LB_InitializeSensor_Addr.errcheck = runtime_error_if_less_than(1)
    LB_API2.LB_BlinkLED_Addr.errcheck = runtime_error_if_less_than(1)

    LB_API2.LB_MeasureCW.errcheck = runtime_error_if_less_than(1)

    LB_API2.LB_SetFrequency.errcheck = runtime_error_if_less_than(1)
    LB_API2.LB_GetFrequency.errcheck = runtime_error_if_less_than(1)
    LB_API2.LB_SetMeasurementPowerUnits.errcheck = runtime_error_if_less_than(1)
    LB_API2.LB_GetMeasurementPowerUnits.errcheck = runtime_error_if_less_than(1)

    LB_API2.LB_SetOffsetEnabled.errcheck = runtime_error_if_less_than(1)
    LB_API2.LB_GetOffsetEnabled.errcheck = runtime_error_if_less_than(1)
    LB_API2.LB_SetOffset.errcheck = runtime_error_if_less_than(1)
    LB_API2.LB_GetOffset.errcheck = runtime_error_if_less_than(1)


def LB_GetAddress_Idx(idx):
    """
    Returns the address of an instrument by ID. 
    
    Parameters
    ----------
    idx : int
    
    Raises
    ------
    RuntimeError
        If no powermeter has such idx.
    """
    return int(LB_API2.LB_GetAddress_Idx(idx))


def LB_InitializeSensor_Addr(addr):
    """ 
    Cause the instrument to be initialized. This typically takes a few seconds.
    
    Parameters
    ----------
    addr : int
        Address of the instrument.
    """
    LB_API2.LB_InitializeSensor_Addr(addr)


def LB_BlinkLED_Addr(addr):
    """ 
    Cause the instrument LED to blink four times. 
    
    Parameters
    ----------
    addr : int
        Address of the instrument.
    """
    LB_API2.LB_BlinkLED_Addr(addr)


psm_models = {
    -1: "unknown",
    101: "PSM4110",
    102: "PSM4120",
    103: "PSM5110",
    104: "PSM5120",
    105: "PSM3110",
    106: "PSM3120",
    107: "PSM3310",
    108: "PSM3320",
    109: "PSM3510",
    110: "PSM4410",
    111: "PSM4320",
    112: "PSM5410",
    113: "PSM5320",
}


def LB_GetModelNumber_Addr(addr):
    """ 
    Get the model number from an address.
    
    Parameters
    ----------
    addr : int
        Address of the instrument.
    
    Returns
    -------
    model : str
    """
    return psm_models[LB_API2.LB_GetModelNumber_Addr(addr)]


#######################################################################################
#           CW MEASUREMENTS
#######################################################################################


def LB_MeasureCW(addr):
    """ Makes CW measurements. The value returned is in the units currently selected. 
    
    Parameters
    ----------
    addr : int
        Address of the instrument.
    
    Returns
    -------
    out : float 
        CW measurement
    """
    CW = c_double()
    result = LB_API2.LB_MeasureCW(addr, CW)
    return float(CW)


#######################################################################################
#           MEASUREMENTS PARAMETERS
#######################################################################################


def LB_SetFrequency(addr, frequency):
    """ This command sets the frequency of the addressed device. It is important
    to note the necessity of setting the frequency to get acurate measurements. 
    
    Parameters
    ----------
    addr : int
        Address of the instrument.
    frequency : float
        Measurement frequency [Hz]
    """
    LB_API2.LB_SetFrequency(addr, frequency)


def LB_GetFrequency(addr):
    """ This command gets the frequency of the addressed device. 
    
    Parameters
    ----------
    addr : int
        Address of the instrument.
    
    Returns
    -------
    out : float
        Measurement frequency [Hz]
    """
    value = c_double()
    LB_API2.LB_GetFrequency(addr, value)
    return float(value)


def LB_SetMeasurementPowerUnits(addr, units):
    """ Set the measurement power units. Valid units are given by:
    DBM = 0, DBW = 1, DBKW = 2, DBUV = 3, W = 4, V = 5, DBREL = 6 
    
    Parameters
    ----------
    addr : int
        Address of the instrument.
    units : int
        Valid units are given by: DBM = 0, DBW = 1, DBKW = 2, 
        DBUV = 3, W = 4, V = 5, DBREL = 6
    """
    LB_API2.LB_SetMeasurementPowerUnits(addr, units)


def LB_GetMeasurementPowerUnits(addr):
    """ Get the measurement power units 
    
    Parameters
    ----------
    addr : int
        Address of the instrument
    
    Returns
    -------
    units : int
        Valid units are given by: DBM = 0, DBW = 1, DBKW = 2, 
        DBUV = 3, W = 4, V = 5, DBREL = 6
    """
    units = c_long()
    err = LB_API2.LB_GetMeasurementPowerUnits(addr, units)
    return int(units)


#######################################################################################
#           OFFSET CONTROL
#######################################################################################


def LB_SetOffsetEnabled(addr, enable):
    """ Enable a fixed offset to be added to the measurements. For an 
    offset that is a function of frequency, use the response function call.
    To set an offset, see LB_SetOffset.
    
    Parameters
    ----------
    addr : int
        Address of the instrument
    enable : bool
        Enable (True) or disable (False)
    """
    LB_API2.LB_SetOffsetEnabled(addr, int(enable))


def LB_GetOffsetEnabled(addr, enable):
    """ Cause a fixed offset to be added to the measurements. For an 
    offset that is a function of frequency, use the response function call 
    
    Parameters
    ----------
    addr : int
        Address of the instrument
    enable : bool
        Enable (True) or disable (False)
    """
    state = c_long()
    LB_API2.LB_GetOffsetEnabled(addr, state)
    return bool(state)


def LB_SetOffset(addr, offset):
    """ Cause a fixed offset to be added to the measurements. For an 
    offset that is a function of frequency, use the response function call.
    To Enable, see LB_SetOffsetEnable
    
    Parameters
    ----------
    addr : int
        Address of the instrument
    offset : float
        Offset in current units.
    """
    LB_API2.LB_SetOffset(addr, offset)


def LB_GetOffset(addr):
    """ Return the fixed offset added to the measurements. For an 
    offset that is a function of frequency, use the response function call.
    To Enable, see LB_SetOffsetEnable
    
    Parameters
    ----------
    addr : int
        Address of the instrument
    
    Returns
    -------
    offset : float
        Offset in current units.
    """
    offset = c_double()
    LB_API2.LB_GetOffset(addr, offset)
    return float(offset)


class TekPSM4120:
    """
    Interface to Tektronix TekPSM4120 RF powermeter.
    
    Parameters
    ----------
    idx : int, optional
        Power-meter ID
    """

    # Conversion between power units and integers
    units_to_num = {
        "dbm": 0,
        "dbw": 1,
        "dbkw": 2,
        "dbuv": 3,
        "w": 4,
        "v": 5,
        "dbrel": 6,
    }
    num_to_units = dict((value, key) for key, value in units_to_num.items())

    def __init__(self, idx=1):
        # Check for successful initialization. If so, blink LEDS
        # If a connection cannot be made, RuntimeError will be raised.
        try:
            self.addr = LB_GetAddress_Idx(idx)
        except:
            raise RuntimeError("PSM instrument not available.")
        LB_InitializeSensor_Addr(self.addr)
        self.blink_led()

        model = LB_GetModelNumber_Addr(self.addr)
        try:
            assert model == "PSM4120"
        except:
            RuntimeError("Unexpected model number: {}".format(model))

        # Set-up default measurement parameters
        self.set_power_units("dBm")

    def blink_led(self):
        """ Blink LEDs four times """
        LB_BlinkLED_Addr(self.addr)

    def measure_cw(self):
        """
        Measure the instantaneous continuous wave (CW) power.

        Returns
        -------
        power : float
            Instantaneous power. Measurement units are given by
            :meth:`TekPSM4120.power_units`. 
        """
        return float(LB_MeasureCW(self.addr))

    @property
    def measurement_frequency(self):
        """ Returns the measurement frequency in GHz """
        return LB_GetFrequency(self.addr) * 1e-9

    def set_measurement_frequency(self, frequency):
        """ 
        Set measurement frequency in GHz. 
        
        Parameters
        ----------
        frequency : float
            Measurement frequency [GHz]
        """
        # LB_SetFrequency takes frequencies in Hz
        LB_SetFrequency(self.addr, float(1e9 * frequency))

    def enable_offset(self, enable):
        """ 
        Enable or disable the measurement offset. 
        
        Parameters
        ----------
        enable : bool
            Activate/deactivate measurement offset.
        """
        LB_SetOffsetEnabled(self.addr, enable)

    def set_offset(self, offset):
        """ Set a measurement offset. The offset must be enabled
        with :meth:`TekPSM4120.enable_offset` 
        
        Parameters
        ----------
        offset : float
            Offset value in current units.
        """
        LB_SetOffset(self.addr, offset)

    @property
    def power_units(self):
        """ measurement power units """
        units = LB_GetMeasurementPowerUnits(self.addr)
        return self.num_to_units[units]

    def set_power_units(self, units):
        """ 
        Set measurement power units.
        
        Parameters
        ----------
        units : str, {'dBm', 'dBw', 'dBkW', 'dBuV','W', 'V', 'dBrel'}
            Power units (case insensitive)
        """
        LB_SetMeasurementPowerUnits(self.addr, self.units_to_num[units.lower()])
