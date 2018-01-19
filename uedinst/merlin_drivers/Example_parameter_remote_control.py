
from MERLIN_connection import *



if __name__ == '__main__':


    print(' - INFO : ')
    print(" - INFO : -------------------------------- ")
    print(" - INFO :   A very simple example of       ")  
    print(" - INFO :  Talking to Merlin via TCP/IP    ")
    print(" - INFO :  Remember to run the MERLIN      ")
    print(" - INFO :  Software on the target machine  ")
    print(" - INFO : -------------------------------- ")
    print(' - INFO :   THIS SOFTWARE WILL ONLY RUN IF NO HEADER IS SENT')
    
    t0 = clock()
    Npulses = 300
    
   
    hostname = '10.0.0.100'
    #hostname = 'diamrd2524'
    # hostname = 'diamrd4048'
    # hostname = 'localhost'
    merlin_cmd = MERLIN_connection(hostname, channel='cmd')
    
    AcqTime = 1
    Numberofimages = 1000
    
    merlin_cmd.setValue('CONTINUOUSRW',1)
    merlin_cmd.setValue('TRIGGERSTART',10)
    merlin_cmd.setValue('TRIGGERSTOP',0)
    
    del merlin_cmd
    
    
