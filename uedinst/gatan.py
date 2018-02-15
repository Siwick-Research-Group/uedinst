
from enum import IntEnum
import socket
from contextlib import AbstractContextManager
from os import remove
from os.path import join
from tempfile import gettempdir

import numpy as np
from skimage.io import imread

from . import InstrumentException

class GatanUltrascan895(AbstractContextManager):
    """
    Interface to the Gatan Ultrascan 895 camera server.

    Parameters
    ----------
    addr : str, optional
        IP address. Default is localhost.
    port : int, optional
    """

    def __init__(self, addr = "127.0.0.1", port = 42057, **kwargs):
        self._socket = socket.socket()
        self._socket.connect((addr, port))
    
    def __exit__(self, *args, **kwargs):
        self._socket.close()
        super().__exit__(*args, **kwargs)
    
    def send_command(self, *commands):
        """
        Send commands to the camera server. This method only returns
        once an answer has been received.
        
        Raises
        ------
        InstrumentException : if answer received indicates an error occurred.
        """
        total_command = ''.join(commands)
        self._socket.send(total_command.encode('ascii'))
        answer = self._socket.recv(10).decode('ascii')

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
    
    def acquire_image(self, exposure, antiblooming = True):
        """ 
        Acquire a gain-normalized image.
        
        Parameters
        ----------
        exposure : float
            Exposure [seconds].
        antiblooming : bool, optional
            If True (default), perform antiblooming.
        
        Returns
        -------
        image : `~numpy.ndarray`

        Raises
        ------
        InstrumentException : if answer received indicates an error occurred.
        """
        exposure = float(exposure)
        antiblooming = str(antiblooming).upper()
        # Use a temporary file so that there can never be any conflits
        # between subsequent acquisitions. The resulting image is read before the file is deleted.
        # Note: we cannot use NamedTemporaryFile because it doesn't create
        # a name, but a file-like object.
        temp_filename = join(gettempdir(), "_uedinst_temp.tif")
        self.send_command("ULTRASCAN;ACQUIRE;{:.3f},{},{}".format(exposure, temp_filename, antiblooming))
        image = imread(temp_filename)
        remove(temp_filename)
        
        return image
