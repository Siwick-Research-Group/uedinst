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
            raise InstrumentException(f"Error: {result}")

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

    def get_position(self):
        x_pos = pyximc.get_position_t()
        result = self.lib.get_position(self.device_id, ct.byref(x_pos))
        self.errcheck(result)
        return x_pos.Position, x_pos.uPosition
    
    def left(self):
        result = self.lib.command_left(self.device_id)
        self.errcheck(result)

    
    def move(self, distance, udistance):
        result = self.lib.command_move(self.device_id, distance, udistance)
        self.errcheck(result)


    def set_speed(self, speed):
        # Create move settings structure
        mvst = pyximc.move_settings_t()
        # Get current move settings from controller
        result = self.lib.get_move_settings(self.device_id, ct.byref(mvst))
        self.errcheck(result)
        # Print command return status. It will be 0 if all is OK
        # Change current speed
        mvst.Speed = int(speed)
        # Write new move settings to controller
        result = self.lib.set_move_settings(self.device_id, ct.byref(mvst))
        # Print command return status. It will be 0 if all is OK
        self.errcheck(result)

    def status(self):
        x_status = pyximc.status_t()
        result = self.lib.get_status(self.device_id, ct.byref(x_status))
        if result == Result.Ok:
            print("Status.Ipwr: " + repr(x_status.Ipwr))
            print("Status.Upwr: " + repr(x_status.Upwr))
            print("Status.Iusb: " + repr(x_status.Iusb))
            print("Status.Flags: " + repr(hex(x_status.Flags)))
        self.errcheck(result)

    def wait_for_stop(self,interval):
        result = self.lib.command_wait_for_stop(self.device_id, interval)
        self.errcheck(result)

    
    def set_microstep_mode_256(self):
        print("\nSet microstep mode to 256")
        # Create engine settings structure
        eng = pyximc.engine_settings_t()
        # Get current engine settings from controller
        result = self.lib.get_engine_settings(self.device_id, ct.byref(eng))
        # Print command return status. It will be 0 if all is OK
        print("Read command result: " + repr(result))
        # Change MicrostepMode parameter to MICROSTEP_MODE_FRAC_256
        # (use MICROSTEP_MODE_FRAC_128, MICROSTEP_MODE_FRAC_64 ... for other microstep modes)
        eng.MicrostepMode = pyximc.MicrostepMode.MICROSTEP_MODE_FRAC_256
        # Write new engine settings to controller
        result = self.lib.set_engine_settings(self.device_id, ct.byref(eng))
        # Print command return status. It will be 0 if all is OK
        self.errcheck(result)

    def set_microstep_mode_FULL(self):
        print("\nSet microstep mode to 256")
        # Create engine settings structure
        eng = pyximc.engine_settings_t()
        # Get current engine settings from controller
        result = self.lib.get_engine_settings(self.device_id, ct.byref(eng))
        # Print command return status. It will be 0 if all is OK
        print("Read command result: " + repr(result))
        # Change MicrostepMode parameter to MICROSTEP_MODE_Full
        # (use MICROSTEP_MODE_FRAC_128, MICROSTEP_MODE_FRAC_64 ... for other microstep modes)
        eng.MicrostepMode = pyximc.MicrostepMode.MICROSTEP_MODE_FULL
        # Write new engine settings to controller
        result = self.lib.set_engine_settings(self.device_id, ct.byref(eng))
        # Print command return status. It will be 0 if all is OK
        self.errcheck(result)

    def stop(self):
        result = self.lib.command_stop(self.device_id)
        self.errcheck(result)

    def right(self):
        result = self.lib.command_right(self.device_id)
        self.errcheck(result)

    def info(self):
        print("\nGet device info")
        x_device_information = pyximc.device_information_t()
        result = self.lib.get_device_information(self.device_id, ct.byref(x_device_information))
        print("Result: " + repr(result))
        if result == Result.Ok:
            print("Device information:")
            print(" Manufacturer: " +
                    repr(pyximc.string_at(x_device_information.Manufacturer).decode()))
            print(" ManufacturerId: " +
                    repr(pyximc.string_at(x_device_information.ManufacturerId).decode()))
            print(" ProductDescription: " +
                    repr(pyximc.string_at(x_device_information.ProductDescription).decode()))
            print(" Major: " + repr(x_device_information.Major))
            print(" Minor: " + repr(x_device_information.Minor))
            print(" Release: " + repr(x_device_information.Release))

    def set_zero(self):
        result = self.lib.command_zero(self.device_id)
        self.errcheck(result)

    def soft_stop(self):
        result = self.lib.command_sstp(self.device_id)
        self.errcheck(result)

    def save_settings(self):
        """save from controllers ram"""
        result = self.lib.command_save_settings(self.device_id)
        self.errcheck(result)

    def load_settings(self):
        """"write to controllers ram"""
        result = self.lib.command_read_settings(self.device_id)
        self.errcheck(result)

    def home_zero(self):
        result = self.lib.command_homezero(self.device_id)
        self.errcheck(result)

    def home(self):
        result = self.lib.command_home(self.device_id)
        self.errcheck(result)
        
    def get_home_settings(self):
        result = self.lib.get_home_settings(self.device_id)
        self.errcheck(result)

    @property
    def get_max_speed(self):
        mtr = pyximc.control_settings_t()
        print(f'Max speed: {ct.byref(mtr.MaxSpeed)}')