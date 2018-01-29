
from contextlib import AbstractContextManager
from enum import IntEnum
from os.path import abspath, join 
from time import sleep

from .merlin_drivers import MERLIN_connection


class Merlin(AbstractContextManager):

    """
    Wrapper around the MERLIN_connection API.

    This API can be used as a context manager:
    >>> with Merlin(...) as merlin:
    ...     pass

    Parameters
    ----------
    hostname : str, optional
    
    ipaddress : str, optional
        (Local) IP address of the Merlin Quad server.
    """
    class DetectorStatus(IntEnum):
        idle    = 0
        busy    = 1
        standby = 2
        armed   = 4

    def __init__(self, hostname = 'diamrd', ipaddress = '169.254.165.189'):
        self._cmd_api  = MERLIN_connection(hostname, ipaddress, channel = 'cmd')

        # Settings most relevant to Siwick Lab
        self._cmd_api.setValue('HVBIAS', 120)               # Never forget to set the bias
        self._cmd_api.setValue('THRESHOLD0', 20)
        self._cmd_api.setValue('THRESHOLD1', 511)
        self._cmd_api.setValue('TRIGGERSTART', 1)           # Starts on rising edge TTL
        self._cmd_api.setValue('TRIGGERSTOP', 0)            # Stops on internal trigger
        self._cmd_api.setValue('NUMFRAMESPERTRIGGER', 1)    # Only acquire one image per trigger
        self._cmd_api.setValue('CHARGESUMMING', 0)          # Charge summing mode off
        self._cmd_api.setValue('FILEENABLE', 1)
    
    def __exit__(self, *args, **kwargs):
        self._cmd_api.setValue('FILEENABLE', 0)
        self._cmd_api.sock.close()
        super().__exit__(*args, **kwargs)
    
    @property
    def sensor_temperature(self):
        """ Immediate sensor temperature in celsius. """
        return self._cmd_api.getFloatNumericVariable('TEMPERATURE')
    
    @property
    def detector_status(self):
        """ Returns the detector status {'idle', 'busy', 'standby'} """
        status = self._cmd_api.getIntNumericVariable('DETECTORSTATUS')
        return self.DetectorStatus(status)
    
    @property
    def hv_bias(self):
        """ High-voltage sensor bias """
        return float(self._cmd_api.getFloatNumericVariable('HVBIAS'))

    @property
    def exposure(self):
        """ Exposure time in seconds """
        ms = self._cmd_api.getFloatNumericVariable('ACQUISITIONTIME')
        return float(ms)/1000
    
    @property
    def acquisition_period(self):
        """ Time of acquisition, which may be multi-frames """
        ms = self._cmd_api.getFloatNumericVariable('ACQUISITIONPERIOD')
        return float(ms)/1000

    def set_folder(self, path):
        """ 
        Change folder in which pictures are saved.
        
        Parameters
        ----------
        path : str
        """
        path = abspath(path)
        return self._cmd_api.setValue('FILEDIRECTORY', path)
    
    def set_filename(self, path):
        """ 
        Change filename in which pictures are saved.
        
        Parameters
        ----------
        path : str
        """
        return self._cmd_api.setValue('FILENAME', path)

    def set_bit_depth(self, depth):
        """ 
        Set the detector bit depth

        Parameters
        ----------
        depth : int, {1, 6, 12, 24}
            Bit depth.
        """
        depth = int(depth)
        assert depth in {1, 6, 12, 24}
        self._cmd_api.setValue('COUNTERDEPTH', depth)

    def set_num_frames(self, num):
        """
        Set the number of frames to take on every acquisition.

        Parameters
        ----------
        num : int
            Number of frames (1 - 100 000)
        """
        num = int(num)
        return self._cmd_api.setValue('NUMFRAMESTOACQUIRE', num)
    
    def set_frames_per_trigger(self, num):
        """
        Set the number of frames to take on every trigger.

        Parameters
        ----------
        num : int
            Number of frames (1 - 100 000)
        """
        num = int(num)
        return self._cmd_api.setValue('NUMFRAMESPERTRIGGER', num)
    
    def set_continuous_mode(self, mode):
        """
        Turn continuous mode ON or OFF.

        Parameters
        ----------
        mode : bool
        """
        mode = int(mode)
        self._cmd_api.setValue('CONTINUOUSRW', mode)
    
    def start_acquisition(self, exposure, period = 1e-3):
        """
        Acquire an image, starting at the next trigger. 

        Parameters
        ----------
        exposure : float
            Exposure time in seconds.
        period : float, optional
            Time between consecutive shots in seconds. Default
            is acquisition at 1 kHz.
        """
        exp_ms = exposure * 1000
        period_ms = period*1000
        self._cmd_api.setValue('ACQUISITIONTIME', exp_ms) 
        self._cmd_api.setValue('ACQUISITIONPERIOD', period_ms)
        self._cmd_api.startAcq()

        while self.detector_status != self.DetectorStatus.idle:
            sleep(0.5)