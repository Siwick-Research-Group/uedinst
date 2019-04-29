import socket
import sys
import re
from time import *
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import struct
from os.path import dirname, join


class MERLIN_connection:

    ENCODING = "ascii"

    def __init__(
        self,
        hostname="diamrd",
        ipaddress="000",
        channel="cmd",
        varFile=join(dirname(__file__), "ListOfCurrentTCPvariables.txt"),
    ):

        self.varsTCPcontrolled = {}
        self.hostname = hostname

        self.listofstringvars = [
            "SOFTWAREVERSION",
            "FLATFIELDFILE",
            "FILEDIRECTORY",
            "FILENAME",
        ]
        self.listofFloatVars = [
            "THSTEP",
            "THSTOP",
            "THSTART",
            "OPERATINGENERGY",
            "THRESHOLD7",
            "THRESHOLD6",
            "THRESHOLD5",
            "THRESHOLD4",
            "THRESHOLD3",
            "THRESHOLD2",
            "THRESHOLD1",
            "THRESHOLD0",
            "TEMPERATURE",
            "HVBIAS",
        ]

        self.listofScientific = ["ACQUISITIONTIME", "ACQUISITIONPERIOD"]

        self.readonly = [
            "TEMPERATURE",
            "DETECTORSTATUS",
            "TriggerInLVDS",
            "TriggerInTTL",
            "SOFTWAREVERSION",
        ]

        # Port number is hardcoded :S
        port = 0

        if channel == "cmd":
            print(" - INFO : Connecting to the command channel")
            port = 6341

        else:
            if channel == "data":
                print(" - INFO : Connecting to the data channel")
                port = 6342
                # self.displayFigure =  plt.figure('Image Display ')

            else:
                print(
                    " - ERROR : Trying to correct to the wrong channel. No rata or command"
                )
                sys.exit()

        # Creating a socket and connection to MERLIN host machine
        print(" - INFO : Connecting  to ", self.hostname)

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            print("Failed to create socket")
            sys.exit()

        try:

            if hostname == "diamrd":
                self.remote_ip = ipaddress
            else:
                self.remote_ip = socket.gethostbyname(self.hostname)

            print(" - INFO : with remote ip ", self.remote_ip)
            server_address = (self.remote_ip, port)
            self.sock.connect(server_address)
            print(" - INFO : Connected to MERKLIN wiith remote ip ", self.remote_ip)

        except socket.gaierror:
            print(" Hostname could not be resolved")
            sys.exit()

        # Creating a local copy of all the 'at this point' default values of Variables
        self._get_list_of_vars(varFile)

        # Putting all the values I get
        if channel == "cmd":
            self.updateValues()

    def __del__(self):

        self.sock.close()
        print(" - INFO :")
        print(" - INFO : Clossing connection to ", self.hostname)
        print(" - INFO :")

    def _get_list_of_vars(self, varFile):

        self.listofTCPvars = []
        with open(varFile) as input:
            for line in input:
                if re.search("#", line):
                    continue
                var = line[:-1].split(" ")[2]
                self.listofTCPvars.append(var)

    def updateValues(self):
        for var in self.listofTCPvars:
            # print ' - INFO : getting ', var
            self.varsTCPcontrolled[var] = self.getVariable(var, PRINT="ON")

        print(" - INFO : ")
        print(" - INFO : This are all the MERLIN default values ")
        for key, val in list(self.varsTCPcontrolled.items()):
            print(" - INFO : ", key, " = ", val)

    def getIntNumericVariable(self, varName, PRINT="OFF"):

        var = 0

        if varName not in self.listofTCPvars:
            print(
                " - WARNING : You are asking for a variable that does not exist ...",
                varName,
            )

        else:

            # Ugly hack... for some reason when getting it does not recognize GAIN but HIGHGAIN
            # that was the original name of the var (for histogical reasons)
            # if varName == 'GAIN' : varName = 'HIGHGAIN'

            cmnd = ",GET,"
            endofcomdn = cmnd + varName

            lenght = len(endofcomdn)

            str_lenght = str(lenght)

            # Two zeros added because the string needs to be at least 15 char
            # if I don't do this the GAIN var fails
            fullcommand = "MPX,00" + str_lenght + endofcomdn
            # 0000000026,GET,NUMFRAMESTOACQUIRE'
            if PRINT == "ON":
                print(" - INFO : sending command ", fullcommand)
            self.sock.send(fullcommand.encode(self.ENCODING))
            data = self.sock.recv(1024).decode(self.ENCODING)
            if PRINT == "ON":
                print(" - INFO : receiving", data)
            var = int(data.split(",")[4])

            res = int(data.split(",")[5])

            if res != 0:
                print(" - ERROR : Something has gone badly ")
                if res == 1:
                    print(" - ERROR : The system is busy ")
                if res == 2:
                    print(" - ERROR : The Command was not recognised ")
                if res == 3:
                    print(" - ERROR : The Paramaeter was out of range ")

        return var

    def getFloatNumericVariable(self, varName, PRINT="OFF"):

        var = 0.0

        if varName not in self.listofTCPvars:
            print(
                " - WARNING : You are asking for a variable that does not exist ...",
                varName,
            )

        else:

            cmnd = ",GET,"
            endofcomdn = cmnd + varName
            lenght = str(len(endofcomdn))

            # Two zeros added because the string needs to be at least 15 char
            # if I don't do this the GAIN var fails
            fullcommand = "MPX,00" + lenght + endofcomdn
            # 0000000026,GET,NUMFRAMESTOACQUIRE'
            if PRINT == "ON":
                print(" - INFO : sending command Float ", fullcommand)
            self.sock.send(fullcommand.encode(self.ENCODING))
            data = self.sock.recv(1024).decode(self.ENCODING)
            if PRINT == "ON":
                print(" - INFO : receiving", data)
            var = float(data.split(",")[4])
            res = int(data.split(",")[5])

            if res != 0:
                print(" - ERROR : Something has gone badly ")
                if res == 1:
                    print(" - ERROR : The system is busy ")
                if res == 2:
                    print(" - ERROR : The Command was not recognised ")
                if res == 3:
                    print(" - ERROR : The Paramaeter was out of range ")
        return var

    def getstringVariable(self, varName, PRINT="OFF"):

        var = ""

        if varName not in self.listofTCPvars:
            print(
                " - WARNING : You are asking for a variable that does not exist ...",
                varName,
            )

        else:
            cmnd = ",GET,"
            endofcomdn = cmnd + varName
            lenght = str(len(endofcomdn))

            # Two zeros added because the string needs to be at least 15 char
            # if I don't do this the GAIN var fails
            fullcommand = "MPX,00" + lenght + endofcomdn
            # 0000000026,GET,NUMFRAMESTOACQUIRE'
            if PRINT == "ON":
                print(" - INFO : sending command String", fullcommand)
            self.sock.send(fullcommand.encode(self.ENCODING))
            data = self.sock.recv(1024).decode(self.ENCODING)
            if PRINT == "ON":
                print(" - INFO : receiving", data)
            var = data.split(",")[4]
            res = int(data.split(",")[5])

            if res != 0:
                print(" - ERROR : Something has gone badly ")
                if res == 1:
                    print(" - ERROR : The system is busy ")
                if res == 2:
                    print(" - ERROR : The Command was not recognised ")
                if res == 3:
                    print(" - ERROR : The Paramaeter was out of range ")
        return var

    def getVariable(self, var, PRINT="OFF"):

        if var in self.listofstringvars:
            return self.getstringVariable(var)

        else:
            if (
                (var in self.listofFloatVars)
                or (var in self.listofScientific)
                or (var in self.readonly)
            ):
                # print ' I AM GETTING HERE', var
                return self.getFloatNumericVariable(var)

            else:
                # print ' BUT ALSO GETTING HERE ? ', var
                return self.getIntNumericVariable(var)

    def setValue(self, varName, value):

        # sleep(1)
        str_value = str(value)

        if varName not in self.listofTCPvars:
            print(
                " - WARNING : You are asking to set a variable that does not exist ...",
                varName,
            )

        else:

            if varName in self.readonly:
                print(" - WARNING :  The variable  ...", varName, " is read only ")

            else:
                cmnd = ",SET,"
                endofcomdn = cmnd + varName + "," + str_value
                lenght = str(len(endofcomdn))

                fullcommand = "MPX,000" + lenght + endofcomdn
                # 0000000026,GET,NUMFRAMESTOACQUIRE'
                print(" - INFO : sending command ", fullcommand)
                # data = self.sock.recv(1024)
                # print ' - INFO : receiving', data

                self.sock.send(fullcommand.encode(self.ENCODING))
                data = self.sock.recv(1024).decode(self.ENCODING)
                print(" - INFO : receiving", data)
                # sleep(1)
                # readback = self.getVariable(varName)
                # print ' - INFO :  ', varName, '    val =  ', str_value , '   readback  = ', readback  ,'    dict =  ',  self.varsTCPcontrolled[varName]
                res = int(data.split(",")[4])

                if res != 0:
                    print(" - ERROR : Something has gone badly ")
                    if res == 1:
                        print(" - ERROR : The system is busy ")
                    if res == 2:
                        print(" - ERROR : The Command was not recognised ")
                    if res == 3:
                        print(" - ERROR : The Paramaeter was out of range ")

                else:
                    # IF proper value I update
                    self.varsTCPcontrolled[varName] = self.getVariable(varName)

    def startAcq(self):

        fullcommand = "MPX,21,CMD,STARTACQUISITION"
        self.sock.send(fullcommand.encode(self.ENCODING))
        data = self.sock.recv(1024).decode(self.ENCODING)
        print(" - INFO : receiving", data)

    def startAcqThresholdScan(
        self, Threshold, acqTime, ini, end, step, fname="default"
    ):

        # Setting variables
        var = "ACQUISITIONTIME"
        val = acqTime
        self.setValue(var, val)

        var = "THSCAN"
        val = Threshold
        self.setValue(var, val)

        var = "THSTART"
        val = ini
        self.setValue(var, val)

        var = "THSTOP"
        val = end
        self.setValue(var, val)

        var = "THSTEP"
        val = step
        self.setValue(var, val)

        var = "THNUMSTEPS"
        val = int((end - ini) / step)
        self.setValue(var, val)
        #############################################

        # Only will enable
        if fname != "default":

            var = "FILEDIRECTORY"
            val = "U:\QualityControl\\test"
            self.setValue(var, val)

            var = "FILENAME"
            val = fname
            self.setValue(var, val)

            # sleep(2)

        #### Executing the command
        fullcommand = "MPX,00011,CMD,THSCAN"
        self.sock.send(fullcommand.encode(self.ENCODING))
        data = self.sock.recv(1024).decode(self.ENCODING)
        print(" - INFO : receiving", data)

    def _GetImageParameters(self, chuck):

        # print  ' - INFOR : ', chuck

        # MPX,<lenght>,   string
        MPXlengh = chuck.split("MQ1")[0]
        size_MPX = sys.getsizeof(MPXlengh)

        # length in bytes from header
        offLEN = int(MPXlengh.split(",")[1])

        # This variables for reading image
        self.bytes = 0
        self.dtype = ""
        self.dtypeM = "uint32"

        # Copy from previous
        # It seems ok as long as I add this 34 but I don't know why!!!!!
        # Only explanation is 33 is the size in python of an emptystring .... sys.getsizeof('')=33
        self.MSGLEN = offLEN + size_MPX - 34

        List = chuck.split(",")

        # print List[:4]
        self.Nx = int(List[6])
        self.Ny = int(List[7])
        LEN = List[8]

        self.lenght = 0

        if re.search("U16", LEN):
            # print ' Enetering here '
            self.dtype = "H"
            self.lenght = 16
            self.bytes = 2

        elif re.search("U32", LEN):
            self.dtype = "I"
            self.lenght = 32
            self.bytes = 4
            # print ' PAssing by here '

        elif re.search("U01", LEN):
            self.lenght = 1
            self.dtype = "B"

        elif re.search("U08", LEN):
            self.lenght = 8
            self.dtype = "B"

        elif re.search("U64", LEN):
            self.lenght = 64

        else:
            if re.search("R64", LEN):
                print(" - Acquiring raw data ")
                self.lenght = int(List[20])
                print(" for bit length ", self.lenght)

            else:
                print(" - ERROR : Wrong bit lenght ")
            sys.exit()

        self.Offset = int(List[4]) + size_MPX - 33
        # print ' - DEBUG : List --> ', List[0:8]
        # print ' - DEBUG : Elements   ',  offLEN, '   ', MPXlengh, '       ' ,  size_MPX, '     ', self.MSGLEN
        # print ' - DEBUG :  Nx  = ', self.Nx
        # print ' - DEBUG :  Ny  = ', self.Ny
        # print ' - DEBUG :  cen = ', LEN
        # print ' - DEBUG :  Offset =', self.Offset
        # print ' - DEBUG :  File length = ', self.MSGLEN
        # print ' - DEBUG :  N bytes =', self.Nx*self.Ny*self.lenght/8

    def _GetMatrix(self, chunk):
        #

        pixelbits = "!" + str(self.Nx * self.Ny) + self.dtype
        # print ' - INFO : pixelbits    ' , pixelbits , ' \n'
        Offset = self.Offset  # +MPX1offset
        matrix = struct.unpack_from(
            pixelbits, chunk, Offset
        )  # MPX1offset+Offset-bytes )

        self.img = np.empty([self.Nx, self.Ny], self.dtypeM)
        # print ' - string size ', sys.getsizeof(chunk)
        for counter in range(0, self.Nx * self.Ny):

            NRow = int(counter / float(self.Nx))
            xpix = NRow
            ypix = counter - NRow * self.Ny

            self.img[xpix][ypix] = matrix[counter]

    def receive_Image(self):

        # print ' - DEBUG : TRYING TO READ IMAGE 1 '
        chunks = []
        # chunks = ''
        bytes_recd = 0

        readbytes = 1024

        self.MSGLEN = 1024
        readbytes = self.MSGLEN
        fistpass = True

        # Main Loop to catch all the data
        while bytes_recd < self.MSGLEN:

            readbytes = min(self.MSGLEN - bytes_recd, readbytes)

            # print ' - DEBUG: Entering the while Loop, Reading ', readbytes , ' bytes '

            chunk = self.sock.recv(readbytes).decode(self.ENCODING)

            # print ' - DEBUG reading first chunk', chunk
            if chunk == "":
                raise RuntimeError(" - ERROR : socket connection broken ")

            # This is a major limitation on acquiring images so should be done elsewhere
            if re.search("HDR", chunk):

                print(" INFO : Header ....", chunk)
                chunk = self.sock.recv(1024).decode(self.ENCODING)
                chunk = ""

            else:
                if fistpass:
                    # This function calculates self.MSGLEN amongst other things
                    # print ' - DEBUG : TRYING TO READ IMAGE 1st PASS '
                    self._GetImageParameters(chunk)

                    # print  '- LENGHT Of file =', self.MSGLEN
                    chunks.append(chunk)
                    fistpass = False

                else:
                    # print ' - INFO: I am getting here because it is NOT the first time '
                    # print ' - DEBUG : TRYING TO READ IMAGE 2nd PASS '
                    chunks.append(chunk)

                bytes_recd = bytes_recd + len(chunk)

        # Here I am Filling the matrix
        # This is a major limitation on acquiring images so should be done elsewhere
        # self._GetMatrix(''.join(chunks))

        return

    def receive_Image_fast(self):

        # print ' - DEBUG : TRYING TO READ IMAGE 1 '
        chunks = []
        # chunks = ''
        bytes_recd = 0
        count = 0

        readbytes = 1024

        self.MSGLEN = 1024
        readbytes = self.MSGLEN
        fistpass = True
        #   For debugging
        # t0=clock()
        t1 = 0.0
        t2 = 0.0
        # Main Loop to catch all the data
        while bytes_recd < self.MSGLEN:

            readbytes = min(self.MSGLEN - bytes_recd, readbytes)

            # print ' - DEBUG: Entering the while Loop, Reading ', readbytes , ' bytes '

            chunk = self.sock.recv(readbytes).decode(self.ENCODING)

            if fistpass:
                # This function calculates self.MSGLEN amongst other things
                # print ' - DEBUG : TRYING TO READ IMAGE 1st PASS '
                # self._GetImageParameters(chunk)
                # t0=clock()
                # This bit is just for testing/debugging... remove later
                self.FirstPassString = chunk

                # This is the working code
                MPXlengh = chunk.split("MQ1")[0]
                size_MPX = sys.getsizeof(MPXlengh)
                # length in bytes from header
                # print ' - CHUCNK ', chunk
                # print ' - MPX  ', MPXlengh
                offLEN = int(MPXlengh.split(",")[1])
                # print offLEN
                self.MSGLEN = offLEN + size_MPX - 34

                # print  '- LENGHT Of file =', self.MSGLENs
                chunks.append(chunk)
                fistpass = False
                # count+=1
                # t1=clock()

            else:
                # print ' - INFO: I am getting here because it is NOT the first time '
                # print ' - DEBUG : TRYING TO READ IMAGE 2nd PASS '
                chunks.append(chunk)

            bytes_recd = bytes_recd + len(chunk)

            # if count < 10 or count > 500:

        # Here I am Filling the matrix
        # self._GetMatrix(''.join(chunks))
        # del chunks
        # t2=clock()
        # # This Bit is just for time testing ----> remember to remove
        # print ' -- '
        # print '  delta 1 ', t1-t0
        # print '  delta 2 ', t2-t1
        # print '  count = ', count
        # print ' - DEBUGGING !!!!!!!! : ---------------------------------------- '
        # t1 = clock()
        # #sprint '\n', self.FirstPassString ,'########'
        # for i in range(0,100000):

        # #This is the working code
        # MPXlengh = self.FirstPassString.split('MQ1')[0]
        # ssize_MPX = sys.getsizeof(MPXlengh)
        # # length in bytes from header
        # offLEN   =  int(self.FirstPassString.split(',')[1])
        # # n = len(self.FirstPassString)
        # t2 = clock()
        # print ' - Time For thiss  two splits (ms)', 1000*(t2-t1)/100000.

        return


if __name__ == "__main__":

    print(" - INFO : ")
    print(" - INFO : -------------------------------- ")
    print(" - INFO :   A very simple example of       ")
    print(" - INFO :  Talking to Merlin via TCP/IP    ")
    print(" - INFO :  Remember to run the MERLIN      ")
    print(" - INFO :  Software on the target machine  ")
    print(" - INFO : -------------------------------- ")
    print(" - INFO :   THIS SOFTWARE WILL ONLY RUN IF NO HEADER IS SENT")

    t0 = clock()
    counter = 0
    Npulses = 2

    hostname = "diamrd2780"
    hostname = "10.0.0.100"
    # hostname = 'diamrd4048'
    # hostname = 'localhost'
    merlinconndata = MERLIN_connection(hostname, channel="data")

    times = []

    for i in range(0, Npulses):

        # timea = clock()

        merlinconndata.receive_Image()

        counter += 1
        if counter < 100:
            print(" Aqcuiqirin image ", i)
            counter = 0
