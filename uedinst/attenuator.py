import ctypes as ct
from contextlib import AbstractContextManager

from . import InstrumentException
from .attenuator_driver import pyximc
from .attenuator_driver.pyximc import Result

PROBE_FLAGS = (
    pyximc.EnumerateFlags.ENUMERATE_ALL_COM + pyximc.EnumerateFlags.ENUMERATE_PROBE
)


class VariableAttenuator(AbstractContextManager):
    """
    Interface to a Standa 8SMC5-USB-B8-1 motor controller
    connected to motorized variable attenuator.
    """

    lib = pyximc.lib

    @classmethod
    def errcheck(cls, result):
        """ Perform error-checking. Raise exception if result is not `Result.Ok` """
        if result != Result.Ok:
            raise InstrumentException(f'Error: {result}')

    def __init__(self, **kwargs):
        devenum = self.lib.enumerate_devices(PROBE_FLAGS, b"")
        dev_count = self.lib.get_device_count(devenum)

        if dev_count > 0:
            # We are assuming that there only ONE suitable device connected to this computer
            # Otherwise, the device index would have to be changed
            device_index = 0
            open_name = self.lib.get_device_name(devenum, device_index)
            self.device_id = self.lib.open_device(open_name)

    def __exit__(self, *args, **kwargs):
        self.close()
        return super().__exit__(*args, **kwargs)

    def close(self):
        self.lib.close_device(ct.byref(ct.cast(self.device_id, ct.POINTER(ct.c_int))))
    
    @property
    def speed(self):
        """ Get motor speed [steps / s]"""
        # TODO: is this motor a stepper motor or a DC motor?
        #       In case of a DC motor, speed is in RPM
        mvst = pyximc.move_settings_t()
        result = self.lib.get_move_settings(self.device_id, ct.byref(mvst))
        self.errcheck(result)
        return mvst.Speed