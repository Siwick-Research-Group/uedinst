import serial

from . import RS485Base, InstrumentException

class KLSeries979(RS485Base):
    """
    Interface to a Kurt Lesker 979 series vacuum transducer.

    Parameters
    ----------
    port : str
        Serial port, e.g. 'COM2'
    kwargs 
        Keyword-arguments are passed to RS485Base class.
    """
    ENCODING = 'ascii'

    def __init__(self, port, **kwargs):
        super().__init__(port = port, 
                         baudrate = 9600, 
                         parity = serial.PARITY_NONE, 
                         stopbits = serial.STOPBITS_ONE,
                         timeout = 1, 
                         **kwargs)

    def read_until(self, termination, **kwargs):
        """
        Read continuously until a certain string.

        Parameters
        ----------
        termination : str

        Returns
        -------
        data : str
        """
        data = ''
        while not data.endswith(termination):
            data += self.read()
        return data
    
    @property
    def baud_rate(self):
        """ Current baud rate """
        self.write('@254BR?;FF')
        value = self.read_until(';FF')
        return int(value[7:-3])
    
    @property
    def degassing(self):
        """ True if transducer is currently degassing; False otherwise. """
        self.write('@254DG?;FF')
        response = self.read_until(';FF')
        return (response == '@254ACKON;FF')
    
    def identify(self):
        """ Flash filament power LED on and off to visually identify
        the unit. """
        self.write('@001TST?;FF')
    
    def degas(self):
        """ 
        Launch degassing procedure. Only possible if pressure
        is below 1e-5 torr.
        
        Raises
        ------
        InstrumentException: if pressure is not low enough. """
        curr_pres = self.pressure()
        if curr_pres > 1e-5:
            raise InstrumentException
        else:
            self.write('@254DG!ON;FF')
            self.read_until(';FF')

    def pressure(self):
        """ 
        Triggers a pressure measurement and returns it immediately

        Returns
        -------
        torr : float
            Instantaneous pressure in Torr 
        """
        self.write('@254PR3?;FF')
        value = self.read_until(';FF')

        # Return value will look like @001ACK1.23E-2;FF
        # Always starts with @xxxACK
        # Always ends in ;FF
        return float(value[7:-3])