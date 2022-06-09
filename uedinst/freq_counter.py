from . import GPIBBase, SerialBase

class TTiTF930(SerialBase):
    """
    Interface to TTi TF930 Frequency Counter.
    
    the frequency currently displayed on the device (valid or not) can be read via the
    frequency property of this class
    """
    def __init__(self, port, **kwargs):
        kwargs.update({"port": port, "baudrate": 115200, "timeout": 1.0})
        super().__init__(**kwargs)
        self.clear()

    def close(self):
        self.clear()
        super().close()

    @property
    def frequency(self):
        self.write_str('?\n')
        return float(self.readline().decode('UTF-8').replace('Hz\r\n', ''))

# class below is obsolete; device physically broke
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
        kwargs["read_termination"] = "\r"
        super().__init__(addr, **kwargs)

        self.write("FA")
        self.write("T0")

    def frequency(self):
        """
        Return the frequency value.

        Returns
        -------
        frequency : float
        """
        raw = self.read()
        return float(raw.replace("FA", ""))
