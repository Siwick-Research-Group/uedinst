import nidaqmx
from . import InstrumentException
from time import sleep


class PCI6281:
    """
    Interface to NI-Data Aquisition PCI-6281.

    """
    
    def __init__(self, *args, **kwargs):
        pass

    def set_voltage(self, value, timeout = None):
        """
        Set voltage on the output channel.

        Parameters
        ----------
        value : float
            Voltage value [V]
        timeout : float or None, optional
            Voltage time-out [s]. If None (default), voltage is assigned indefinitely.
        
        Raises
        ------
        InstrumentException : if voltage `value` is outside of += 10V.
        """
        value = float(value)
        if abs(value) > 10:
            raise InstrumentException(f'Voltage {value} is outside of permissible bounds of +=10V')
        
        if timeout is not None:
            if timeout <=0:
                raise InstrumentException(f"A time-out value of {timeout} seconds is not valid.")
        
        
        with nidaqmx.Task() as task: 
            task.ao_channels.add_ao_voltage_chan('Dev1/ao1')
            task.write(value)
            task.stop()
            if timeout is not None:
                sleep(timeout)
                task.write(0)
                task.stop()