
import socket
from contextlib import AbstractContextManager
from os.path import join
from tempfile import gettempdir
from time import sleep

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
        IP port.
    """

    def __init__(self, addr = "127.0.0.1", port = 42057, **kwargs):
        self._socket = socket.socket()
        try:
            self._socket.connect((addr, port))
        except ConnectionRefusedError:
            raise InstrumentException('Could not connect to Digital Micrograph. Make sure it is open.')
    
    def __exit__(self, *args, **kwargs):
        self._socket.close()
        super().__exit__(*args, **kwargs)
    
    def send_command(self, *commands, wait = 0):
        """
        Send commands to the camera server. This method only returns
        once an answer has been received.
        
        Raises
        ------
        InstrumentException : if answer received indicates an error occurred.
        """
        total_command = ''.join(commands)
        self._socket.send(total_command.encode('ascii'))
        sleep(wait)
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
    
    def acquire_image(self, exposure):
        """ 
        Acquire a fully-processed image.
        
        Parameters
        ----------
        exposure : float
            Exposure [seconds].
        
        Returns
        -------
        image : `~numpy.ndarray`

        Raises
        ------
        InstrumentException : if answer received indicates an error occurred.
        """
        # Use a temporary file so that there can never be any conflits
        # between subsequent acquisitions. The resulting image is read before the file is deleted.
        # Note: we cannot use NamedTemporaryFile because it doesn't create
        # a name, but a file-like object.
        temp_filename = join(gettempdir(), "_uedinst_temp.tif")
        self.acquire_image_to_file(temp_filename, exposure)
        image = imread(temp_filename)
        return image[:,:,0] # For some reason, images are read as color images
    
    def acquire_image_to_file(self, filename, exposure):
        """ 
        Acquire a fully-processed image and save directly to file.
        
        Parameters
        ----------
        filename : str or path-like
            Absolute path to a file.
        exposure : float
            Exposure [seconds].

        Raises
        ------
        InstrumentException : if answer received indicates an error occurred.

        See Also
        --------
        acquire_image : acquire an image as a NumPy array
        """
        exposure = float(exposure)
        filename = str(filename)
        self.send_command("ULTRASCAN;ACQUIRE;{:.3f},{}".format(exposure, filename), wait = exposure)
