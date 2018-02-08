
import socket
from contextlib import AbstractContextManager, suppress

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
        # TODO: if socket cannot connect, launch camera_server.s somehow
        #       See gatan scripting documentation on how to launch scripts from
        #       external process.
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
        RuntimeError : if answer received indicates an error occurred.
        """
        total_command = ''.join(commands)
        self._socket.send(total_command.encode('utf-8'))
        answer = self._socket.recv(10).decode('utf-8')

        if answer != 'OK':
            raise RuntimeError('Command failed: {}. \n Answer received: {}'.format(total_command, answer))
        
        return answer

    def insert(self, toggle):
        """
        Insert/uninsert into the beam.

        Parameters
        ----------
        toggle : bool
            If True, the camera will insert; otherwise, the camera will uninsert.
        """
        toggle = str(toggle).upper()
        self.send_command('ULTRASCAN:INSERT:', toggle)
