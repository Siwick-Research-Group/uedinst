
import socket
from contextlib import AbstractContextManager
from os.path import join
from tempfile import gettempdir
from time import sleep

from skimage.io import imread

import numpy as np
from . import TCPBase, InstrumentException

class GatanUltrascan895(TCPBase):
    """
    Interface to the Gatan Ultrascan 895 camera server.

    Parameters
    ----------
    addr : str, optional
        IP address. Default is localhost.
    port : int, optional
        IP port.
    """
    def __init__(self, *args, **kwargs):
        try:
            super().__init__('127.0.0.1', 42057)
        except InstrumentException:
            raise InstrumentException('Could not connect to DigitalMicrograph. Make sure it is open.')
    
    def send_command(self, *commands, wait = 0):
        """
        Send commands to the camera server. This method only returns
        once an answer has been received.
        
        Raises
        ------
        InstrumentException : if answer received indicates an error occurred.
        """
        total_command = ''.join(commands)
        self.socket.send(total_command.encode('ascii'))
        sleep(wait)
        answer = self.socket.recv(10).decode('ascii')

        if answer == "ERR":
            raise InstrumentException('Command failed: {}. \n Answer received: {}'.format(total_command, answer))
        
        return answer

    def insert(self, toggle):
        """
        Insert/uninsert into the beam.

        Parameters
        ----------
        toggle : bool
            If True, the camera will insert; otherwise, the camera will uninsert.

        Raises
        ------
        InstrumentException : if answer received indicates an error occurred.
        """
        toggle = str(toggle).upper()
        self.send_command('ULTRASCAN;INSERT;', toggle)
    
    def acquire_image(self, exposure):
        """ 
        Acquire an image from the detector.
        
        Parameters
        ----------
        exposure : float
            Exposure [seconds].
        
        Returns
        -------
        image : `~numpy.ndarray`, dtype int16
            Gain-normalized, dark-background subtracted image.

        Raises
        ------
        InstrumentException : if answer received indicates an error occurred.
        """
        exposure = float(exposure)
        # Use a temporary file so that there can never be any conflits
        # between subsequent acquisitions.
        # Note: we cannot use NamedTemporaryFile because it doesn't create
        # a name, but a file-like object.
        temp_filename = join(gettempdir(), "_uedinst_temp.dat")
        self.send_command("ULTRASCAN;ACQUIRE;{:.3f},{}".format(exposure, temp_filename), wait = exposure)

        # We save the images as raw format
        # because the 'translation' to TIFF was buggy
        # Therefore, better to get to the raw data and cast ourselves.
        with open(temp_filename, mode = 'rb') as datafile:
            arr = np.fromfile(datafile, dtype = np.int32).reshape((2048, 2048))
        
        # Gatan Ultrascan 895 can't actually detect higher than ~30 000 counts
        # Therefore, we can safely cast as int16 
        # First, clipping to minimum/maximum int16 is done 
        int16info = np.iinfo(np.int16)
        np.clip(arr, int16info.min, int16info.max, out = arr)
        return arr.astype(np.int16)
