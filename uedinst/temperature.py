
from enum import IntEnum
from time import sleep

from . import GPIBBase, InstrumentException

class ITC503(GPIBBase):
    """
    Interface to an ITC 503 intelligent temperature controller.

    The preferred way of using this object is through context management:
    >>> with ITC503() as tempcontroller:
    ...     pass
    
    Otherwise, do not forget to change the control level through ``ITC503.set_control``.
    """
    class ControlState(IntEnum):
        LocalLocked    = 0  # Default state
        RemoteLocked   = 1
        LocalUnlocked  = 2
        RemoteUnlocked = 3
    
    class HeatAndFlowMode(IntEnum):
        AllManual             = 0
        HeaterAutoGasManual   = 1
        HeaterManualGasAuto   = 2
        AllAuto               = 3

    def __init__(self, **kwargs):
        kwargs.update({'read_termination' : '\r',
                       'write_termination': '\r'})
        super().__init__(addr = 'GPIB::24', **kwargs)

        # Put ITC503 in GPIB IN_USE mode
        self._instrument.control_ren(1)

        # Without a small delay between the follow two 
        # operations, the ITC503 can freeze
        self.clear()
        sleep(0.5)  
        self.set_control(3)
    
    def query(self, *args, **kwargs):
        """ The OXFORD ITC 503 specifically triggers the SRQ when the full response is available """
        self.write(*args, **kwargs)
        self.wait_for_srq()
        return self.read()

    def set_control(self, state):
        """
        Set the level of control.

        Parameters
        ----------
        state : ITC503.ControlState instance
        """
        try:
            state = self.ControlState(state)
        except:
            raise InstrumentException('Unexpected state: ', str(state))

        # By using $, we tell the ITC503 to not issue a response.
        self.query('C{:d}'.format(int(state)))
    
    @property
    def control_state(self):
        status = self.query('X') # = 'X0A0C0S00H1L0'
        if not status:
            self.clear()
            raise InstrumentException('Control state was not returned.')
        return self.ControlState(int(status[5]))
    
    @property
    def heater_and_gas_flow(self):
        """ State of heater and gas flow control """
        status = self.query('X') # = 'X0A0C0S00H1L0'
        return self.HeatAndFlowMode(int(status[3]))
    
    @property
    def temperature(self):
        """ Instantaneous temperature of sensor 1 in Kelvin """
        message = self.query('R1')
        return float(message[1:])
    
    @property
    def temperature_setpoint(self):
        """ Return temperature setpoint in Kelvin. """
        message = self.query('R0')  # = 'R391.2'
        return float(message[1:])
    
    def set_temperature(self, setpoint):
        """
        Change temperature setpoint.

        Parameters
        ----------
        setpoint : float
            Temperature setpoint in Kelvins.
        
        Raises
        ------
        InstrumentException : If temperature setpoint could not be changed.
        """
        self.query('T{:3.2f}'.format(setpoint))

        if self.temperature_setpoint != setpoint:
            self.clear()
            raise InstrumentException('Temperature setpoint was not set properly.',
                                      'Make sure the control level has been set properly.')