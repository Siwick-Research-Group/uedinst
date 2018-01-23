
from contextlib import closing
from uedinst import Merlin
import socket
from os.path import join
from time import sleep

TIME_POINTS = [-50, -25, 0, 25, 50, 100]
EXPOSURE    = 3.0
FOLDER      = 'D:\\Data\\Test'

if __name__ == '__main__':

    sock = socket.socket()
    sock.connect(('127.0.0.1', 42056))

    with closing(sock):

        sock.send(b'PUMPSHUTTER:CONNECT:TRUE')
        assert sock.recv(10).decode() == 'OK'
        sleep(10)
            
        # Move stage to time-zero to start
        sock.send(b'DELAYSTAGE:CONNECT:TRUE')
        sock.recv(10).decode()
        sleep(10)

        sock.send(b'DELAYSTAGE:ABS_TIME_SHIFT: 0.0')
        sock.recv(10).decode()

        with Merlin() as merlin:
            merlin.set_folder(FOLDER)

            for time in TIME_POINTS:

                message = 'DELAYSTAGE:ABS_TIME_SHIFT:{}'.format(time)
                sock.send(message.encode('utf-8'))
                sock.recv(10).decode()

                sock.send(b'PUMPSHUTTER:ENABLE:TRUE')
                sock.recv(10).decode()
                sleep(5)

                merlin.set_filename('pumpon_{}ps.mib'.format(time))
                merlin.start_acquisition(EXPOSURE)
                sleep(EXPOSURE + 0.5)

                sock.send(b'PUMPSHUTTER:ENABLE:FALSE')
                sock.recv(10).decode()
                sleep(5)

                merlin.set_filename('pumpoff_{}ps.mib'.format(time))
                merlin.start_acquisition(EXPOSURE)
                sleep(EXPOSURE + 0.5)

                
            