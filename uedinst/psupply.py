
from . import SerialBase, InstrumentException

class HeinzingerPNChp(SerialBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        identity = self.query('*IDN?')
        if 'PNChp150000' not in identity:
            raise InstrumentException('Connected instrument is not a power supply: {}'.format(identity))
        
        self.write('AVER 16')
    
    @property
    def measured_voltage(self):
        """ Instantaneous measured voltage in kV """
        return float(self.query('MEAS:VOLT?'))
    
    @property
    def voltage_setpoint(self):
        """ Voltage setpoint in kV """
        return float(self.query('VOLT?'))

    @property
    def measured_current(self):
        """ Instantaneous measured current in mA """
        return float(self.query('MEAS:CURR?'))
    
    @property
    def current_setpoint(self):
        """ Current setpoint in mA """
        return float(self.query('CURR?'))
    
    def enable_output(self, toggle):
        """
        Toggle the power supply output.

        Parameters
        ----------
        toggle : bool
            If True, output is enabled. If False, output is disabled.
        """
        cmd = 'OUTP ON' if toggle else 'OUTP OFF'
        self.write(cmd)
    
    def set_voltage(self, voltage):
        """ 
        Set nominal voltage.
        
        Parameters
        ----------
        voltage : float
            Desired nominal voltage in kV.
        """
        self.write('VOLT {}'.format(voltage))

    def set_current(self, current):
        """         
        Set nominal current.
        
        Parameters
        ----------
        current : float
            Desired nominal current in mA. 
        """
        self.write('CURR {}'.format(current))