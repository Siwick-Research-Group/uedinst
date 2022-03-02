# -*- coding: utf-8 -*-
"""
BPIB interface for ITC503 remote control 
Version: 1.0.0

built from 'temperature.py' in uedinst ~< 1.3.2 
added:
* set_heater_and_gas_flow()
* heater_power
* gas_flow
* set_heater_power
* set_gas_flow
* emergency_stop
"""

from enum import IntEnum
from time import sleep
from math import floor



from . import GPIBBase, InstrumentException



gpib_address = 24


class ITC503(GPIBBase):
    """
    Interface to an ITC 503 intelligent temperature controller.

    The preferred way of using this object is through context management:
    >>> with ITC503() as tempcontroller:
    ...     pass
    
    Otherwise, do not forget to change the control level through ``ITC503.set_control``.
    """

    class ControlState(IntEnum):
        LocalLocked = 0  # Default state
        RemoteLocked = 1
        LocalUnlocked = 2
        RemoteUnlocked = 3

    class HeaterAndFlowMode(IntEnum):
        AllManual = 0
        HeaterAutoGasManual = 1
        HeaterManualGasAuto = 2
        AllAuto = 3

    def __init__(self, **kwargs):
        kwargs.update({"read_termination": "\r", "write_termination": "\r"})
        super().__init__(addr="GPIB::{}".format(str(gpib_address)), **kwargs)

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
            raise InstrumentException("Unexpected state: ", str(state))
            return

        # By using $, we tell the ITC503 to not issue a response.
        self.query("C{:d}".format(int(state)))
    
    def set_heater_and_gas_flow(self, mode):
        """
        Set heater and gas flow control state.

        Parameters
        ----------
        state : ITC503.HeaterAndFlowMode instance
        """
        try:
            mode = self.HeaterAndFlowMode(mode)
        except:
            raise InstrumentException("Unexpected Heater and Gas Flow State: ", str(mode))
            return
        
        self.query("A{:d}".format(int(mode)))

    @property
    def control_state(self):
        status = self.query("X")  # = 'X0A0C0S00H1L0'
        if not status:
            self.clear()
            raise InstrumentException("Control state was not returned.")
        return self.ControlState(int(status[5]))

    @property
    def heater_and_gas_flow(self):
        """ State of heater and gas flow control """
        status = self.query("X")  # = 'X0A0C0S00H1L0'
        return self.HeaterAndFlowMode(int(status[3]))

    @property
    def temperature(self):
        """ Instantaneous temperature of sensor 1 in Kelvin """
        message = self.query("R1")
        return float(message[1:])
    
    @property
    def heater_power(self):
        """ heater power as 1 in volts """
        message = self.query("R6")
        return float(message[1:])
    
    @property
    def gas_flow(self):
        """ gas flow as 1 in a.u. --> will be specified later """
        message = self.query("R7")
        return float(message[1:])

    @property
    def temperature_setpoint(self):
        """ Return temperature setpoint in Kelvin. """
        message = self.query("R0")  # = 'R391.2'
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
        InstrumentException : If 
        InstrumentException : If temperature setpoint could not be changed.
        """
        self.query("T{:3.2f}".format(setpoint))

        if self.temperature_setpoint != setpoint:
            self.clear()
            raise InstrumentException(
                "Temperature setpoint was not set properly.",
                "Make sure the control level has been set properly.",
            )
    
    def set_heater_power(self, power):
        """
        Change heater output power

        Before the heater output can be changed on the ITC503 the heater control has to be switched to manual. Use heater_and_gas_flow to check control mode and set_heater_and_gas flow to change control mode

        Parameters
        ----------
        power : float
            Heater output in percent between 0% and 99.9% with resolution of .1%

        Raises
        ------
        Intrument Exception : If power setpoint is not in valid range
        InstrumentException : If heater output power could not be changed.

        """
        
        if power <0 or power >= 100:
            raise InstrumentException("Power input has to be between 0% and 99.9%")
        else:
            self.query("O{:.1f}".format(floor(power*10)/10))
        message = self.query("R5")
        heater_power_pc = float(message[1:])
        if heater_power_pc != floor(power*10)/10:
            self.clear()
            raise InstrumentException(
                "Heater power has not been set properly.",
                "Make sure the control level has been set properly.",
            )
        
            
    def set_gas_flow(self, flow):
        """
        Change gas flow by operating motorized needle valve

        Before the gas flow can be changed on the ITC503 the gas flow control has to be switched to manual. Use heater_and_gas_flow to check control mode and set_heater_and_gas flow to change control mode

        Parameters
        ----------
        power : float
            flow in percent of needle valve open between 0% and 99.9% with resolution of .1%

        Raises
        ------
        Intrument Exception : If flow setpoint is not in valid range
        InstrumentException : If flow setpoint could not be changed.

        """
        if flow <0 or flow >= 100:
            raise InstrumentException("Flow input has to be between 0% and 99.9%")
        else:
            self.query("O{:.1f}".format(floor(flow*10)/10))
        if self.gas_flow != floor(flow*10)/10:
            self.clear()
            raise InstrumentException(
                "Flow parameter has not been set properly.",
                "Make sure the control level has been set properly.",
            )
            

    def emergency_stop(self):
        """
        Peforms an emergency stop of the remote control of the heater:
        - Heater Output is set to ZERO
        - Needle Valve Gas Flow is set to ZERO
        - Control State is set to LOCAL & UNLOCKED

        Returns
        -------
        None.

        """
        # get Heat and Flow Mode
        status = self.query("X")
        state = self.HeaterAndFlowMode(int(status[3]))
        if state.value == 0:
            pass
        else:
            # Set heater and gas flow to manual control to allow for manual adjustment
            self.set_heater_and_gas_flow(0)
        # Set heater power and gas flow to 0 and switch to Local&Unlocked control
        self.set_heater_power(0)
        self.set_gas_flow(0)
        self.set_control(2)