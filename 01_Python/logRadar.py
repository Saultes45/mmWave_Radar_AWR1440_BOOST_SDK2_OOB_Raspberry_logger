#!/usr/bin/env python3

# -------------------Metadata----------------------
# Creator: Nathanael ESNAULT

# nathanael.esnault@gmail.com
# or
# nesn277@aucklanduni.ac.nz

# Creation date 2022-05-02
# Version	1.0

# Version Control: https://github.com/Saultes45/


# -------------------bash----------------------


# source: https://serverfault.com/questions/103501/how-can-i-fully-log-all-bash-scripts-actions
# #!/bin/bash
# exec 3>&1 4>&2
# trap 'exec 2>&4 1>&3' 0 1 2 3
# exec 1>log.out 2>&1
# # Everything below will go to the file 'log.out':
#
# echo "$(date) : part 1 - start" >&3

#
# OR
#
# source: https://askubuntu.com/questions/1299066/print-bash-script-output-to-log-file
# ./yourScript.sh 2>&1 | tee info.log



# -------------------VERY important notes----------------------
# Clear console
# os.system('printf "\033c"')

# You need 2 sub-folders in the root folder and a python module
# one called "01_LoggerParameters" for the python script parameters
# one called "02_RadarParameters" for the containing the radar commands to put it in the correct configuration
# the python module "globals.py" contains no code but global variables


# When calling "sensorStart" you might receive a "Debug: Init Calibration Status = 0x7fe" answer: all good!
# The 0x7fe status code is a passing value - it is a bit field that is indicating all calibration tasks have passed.

# Why not swap INI files for JSON (native support from python)?
# Have a second short log for execution info (version, working directory, errors, etc)


# TODO: put radar config profile in a class (configParameters)

# -----------------------Package version -------------------------------------------

# Python interpreter: 3.7.X (Home desktop win7 x64) or 3.7.3 (Uni PGR desktop)
#
# You also need to install the following libraries (pip if IDLE or if PyC Toolbar->File->Setting-> Project interpreter)
# --> pyserial V3.5 (latest at the time)
# --> numpy V1.22.3 (latest at the time)

# ---------------------- imports -----------------------------------------
import configparser ## for reading the logger data stored in the Parameters.ini file
import os           ## for managing files and directories
import subprocess   ## for checking the USB drive is present on the RPi
import platform     ## for checking the platform (Win7 or raspberry pi)
import serial       ## to communicate with the TI radar AWR1443BOOST

import glob         ## for Linux platform only: list available serial ports
import time         ## to slow down the data sent via serial

import logging                                    ## for logging both data and debug log
from logging.handlers import RotatingFileHandler  ## for limiting the file size

import numpy as np  ## for parsing the radar data
# import re  ## for find substr in str

import globals  ## for storing my global variables that cannot be put in the ini file


# ---------------------- user-defined exceptions [1+2]------------------

# source: https://www.programiz.com/python-programming/user-defined-exception
class Error(Exception):
    """Base class for other exceptions"""
    pass


class USBNotRecognised(Error):
    """Raised when the the USB is not plugged in th Raspberry Pi"""
    # pass
    print("Could not find a USB drive, stopping execution")
    print(globals.crashMarker)


class BadOS(Error):
    """Raised when the code is executed on an OS which neither Windows or Linux"""
    # pass
    print("Unknown OS, stopping execution")
    print(globals.crashMarker)

# ---------------------- Class [4]------------------

class RadarDetectedObject:
    def __init__(self):
        self.echoNumber = 999
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.velocity = 0.0
        self.rangeIdx = 0
        self.rangeVal = 0.0
        self.dopplerIdx = 0
        self.dopplerVal = 0.0
        self.peakVal = 0
        self.isValid = False
        self.isConverted = False
        self.elv = 0.0
        self.azmth = 0.0

class RadarFrameHeader:
    def __init__(self):
        self.magicNumber = [0, 0, 0, 0, 0, 0, 0, 0]
        #self.version = "0.0.1"
        self.sdkVersion = SDKversion()  # another class
        self.totalPacketLen = 0
        self.platform = 0  # a1443
        self.frameNumber = 0
        self.timeCpuCycles = np.uint32(4294967295)
        self.numDetectedObj = 0
        self.numTLVs = 0

class RadarData:
    def __init__(self):
         self.binData = []
         self.magicOK = False
         self.dataOK = False
         self.frmhdr = RadarFrameHeader()
         self.tlv_xyzQFormat = 0
         self.objList = []  # to have different pointers, "append" is used later
         # self.objList = [RadarDetectedObject()] * globals.nbrStoredEchoesInClass  # Max number of stored echo objects


class SDKversion:
    # SDK Version represented as (MajorNum x 2^24 + MinorNum x 2^16 + BugfixNum x 2^8 + BuildNum)
    def __init__(self):
        self.MajorNum = 255
        self.MinorNum = 255
        self.BugfixNum = 255
        self.BuildNum = 255

# ---------------------- global variables [5]------------------

## Is it really the best way to keep the buffer between 2 radar frames? --> Yes for now
#global byteBuffer, byteBufferLength

byteBuffer = np.zeros(2**15, dtype='uint8')
byteBufferLength = 0

# ---------------------- functions [17]-----------------------------------------

# ***********************************************************************************************************************
def addPointCloudsToClass(classToAdd, nbr_points):
    ### Function to add point cloud classes in the list of point cloud held by the radar class

    #  Make sure we don't add too many
    nbr_points = min(globals.nbrStoredEchoesInClass, nbr_points)

    for _ in range(nbr_points):  # Max number of stored echo objects, notice throw-away variable
        classToAdd.objList.append(RadarDetectedObject())

    return classToAdd

    ## END OF FUNCTION
# ***********************************************************************************************************************

# ***********************************************************************************************************************
def displayDebugData(runID):
    ### Function to print on console (maybe logged by bash script) data about exec for EZ debug


    print("-"*50)

    print("logRadar.py script starts with ID: {}".format(runID))


    CurrentOS = platform.system()
    if (CurrentOS == 'Windows' or CurrentOS == 'win32'):
        print("You are using Windows")
    elif CurrentOS == 'Linux':
        print("You are using Linux")
    else:
        # Unknown OS
        raise BadOS

    # Get the current working directory
    cwd = os.getcwd()

    # Print the current working directory
    print("Current working directory: {0}".format(cwd))

    print("-" * 50)


    ## END OF FUNCTION
# ***********************************************************************************************************************

# ***********************************************************************************************************************
def executeShellAsSudo(command):
    ### Function to execute the input command as sudo
    ### As you could fear, it is super insecure and definitely a BAD idea
    ### And the cherry on top is: we hard code the sudo password
    ### The cream is: this is the default raspberry pi password
    ### Use at your own risks

    # source: https://stackoverflow.com/questions/567542/running-a-command-as-a-super-user-from-a-python-script
    sudo_password = 'raspberry'
    command = command.split()

    cmd1 = subprocess.Popen(['echo', sudo_password], stdout=subprocess.PIPE)
    cmd2 = subprocess.Popen(['sudo', '-S'] + command, stdin=cmd1.stdout, stdout=subprocess.PIPE)

    output = cmd2.stdout.read().decode()

    return output
    ## END OF FUNCTION
# ***********************************************************************************************************************


#***********************************************************************************************************************
def postprocessData14xx(parsedData, configParameters):
    ### Function to apply the corrections to the data that have been parsed
    ### This function should be called just after "readAndParseData14xx"


    # Step#1 - Make the necessary corrections and calculate the rest of the data (3)
    # --------------------------------------------------------------------------------

    for objectNum in range(parsedData.frmhdr.numDetectedObj):
        try:
            # Correction on distances - 1/3
            #------------------------------
            parsedData.objList[objectNum].x = parsedData.objList[objectNum].x / parsedData.tlv_xyzQFormat
            parsedData.objList[objectNum].y = parsedData.objList[objectNum].y / parsedData.tlv_xyzQFormat
            parsedData.objList[objectNum].z = parsedData.objList[objectNum].z / parsedData.tlv_xyzQFormat

            # Correction on range - 2/3
            # --------------------------
            parsedData.objList[objectNum].rangeVal = \
                parsedData.objList[objectNum].rangeIdx * configParameters["rangeIdxToMeters"]

            # Correction on doppler - 3/3
            # ------------------------------
            # The following monstrosity (from what I could understand at least) uses the equivalence True = 1 and
            # False = 0 as indexes, commented out until I understand better

            # calculate azimuth/elevation AND range (rectangular to spherical coordinates)

            #parsedData.objList[objectNum].dopplerIdx[parsedData.objList[objectNum].dopplerIdx > (configParameters["numDopplerBins"] / 2 - 1)] = parsedData.objList[objectNum].dopplerIdx[parsedData.objList[objectNum].dopplerIdx > (configParameters["numDopplerBins"] / 2 - 1)] - 65535

            parsedData.objList[objectNum].dopplerVal = parsedData.objList[objectNum].dopplerIdx * configParameters[
                "dopplerResolutionMps"]

            # first 1/2 of the bins are >0 (no change) and the second 1/2 are <0 (-65535)
            # if parsedData.objList[objectNum].dopplerIdx < (configParameters["numDopplerBins"] / 2 - 1):
            #     parsedData.objList[objectNum].dopplerVal = parsedData.objList[objectNum].dopplerVal - 65535


            # x[x > 32767] = x[x > 32767] - 65536
            # y[y > 32767] = y[y > 32767] - 65536
            # z[z > 32767] = z[z > 32767] - 65536

            # indicate we performed the post-processing on that object
            parsedData.objList[objectNum].isConverted = True


            # Step#2 - Filter echoes to only get the water elevation
            # -------------------------------------------------------


            # Sort the azimuth - 1/3 configParameters["azimuthThreshold"]
            # Sort the velocity( or doppler?) - 2/3 configParameters["velocityThresholdMin"] configParameters["velocityThresholdMax"]
            # Sort the range - 3/3 configParameters["rangeThresholdMin"] configParameters["rangeThresholdMax"]
            # Sort the SNR or RSSI - peakVal

        # when there is an error on a point cloud, just leave "isConverted" as False and continue trying
        except Exception as inst:
            print(type(inst))  # the exception instance
            print(inst.args)  # arguments stored in .args
            print(inst)
            pass

    return parsedData
    ## END OF FUNCTION
# ***********************************************************************************************************************

#***********************************************************************************************************************
def readAndParseData14xx(Dataport):
    ### Function to read and parse the incoming radar data

    global byteBuffer, byteBufferLength

    # instantiate an empty class-struct to store the retrieved data
    parsedData = RadarData()
    parsedData = addPointCloudsToClass(parsedData, globals.nbrStoredEchoesInClass)

    # Constants
    #------------
    # TODO: all of those should be in the ini file
    MMWDEMO_UART_MSG_DETECTED_POINTS = 1
    # 1 Detected Points
    # 2 Range Profile
    # 3 Noise Floor Profile
    # 4 Azimuth Static Heatmap
    # 5 Range-Doppler Heatmap
    # 6 Statistics (Performance)
    # 7 Side Info for Detected Points
    # 8 Azimuth/Elevation Static Heatmap
    # 9 Temperature Statistics

    # var
    # TLV_type = {
    #     MMWDEMO_OUTPUT_MSG_DETECTED_POINTS: 1,
    #     MMWDEMO_OUTPUT_MSG_RANGE_PROFILE: 2,
    #     MMWDEMO_OUTPUT_MSG_NOISE_PROFILE: 3,
    #     MMWDEMO_OUTPUT_MSG_AZIMUT_STATIC_HEAT_MAP: 4,
    #     MMWDEMO_OUTPUT_MSG_RANGE_DOPPLER_HEAT_MAP: 5,
    #     MMWDEMO_OUTPUT_MSG_STATS: 6,
    #     MMWDEMO_OUTPUT_MSG_MAX: 7
    # };

    maxBufferSize = 2 ** 15  # in bytes
    expectedMagicWord = [2, 1, 4, 3, 6, 5, 8, 7]
    minAcceptableBuffSize = 16

    # word array to convert 4 bytes to a 32 bit number
    word_4_32 = [2 ** 0, 2 ** 8, 2 ** 16, 2 ** 24]
    # word array to convert 4 bytes to a 16 bit number
    word_4_16 = word_4_32[:2]
    # word array to convert 4 bytes to a 8 bit number
    word_4_8 = word_4_32[:1]


    ## Nate: Read data from the radar DATA serial data port
    readBuffer = Dataport.read(Dataport.in_waiting)
    byteVec = np.frombuffer(readBuffer, dtype='uint8')
    del readBuffer
    byteCount = len(byteVec)  # Nate: count how many bytes have been received through the serial port

    # Check that the buffer is not full, and then add the data to the buffer
    if (byteBufferLength + byteCount) < maxBufferSize:
        byteBuffer[byteBufferLength:byteBufferLength + byteCount] = byteVec[:byteCount]
        byteBufferLength = byteBufferLength + byteCount

    # Check that the buffer has some data
    if byteBufferLength > minAcceptableBuffSize:

        # Check for all possible locations of the magic word
        possibleLocs = np.where(byteBuffer == expectedMagicWord[0])[0]  # look for the first char only

        # Confirm if the occurrences found are indeed the beginning of a magic word, store the index in startIdx if True
        startIdx = []
        for loc in possibleLocs:
            check = byteBuffer[loc:loc + 8]
            if np.all(check == expectedMagicWord):
                startIdx.append(loc)

        ## Check if the magic number is good
        parsedData.magicNumber = byteBuffer[startIdx[0]:startIdx[0] + 8]
        parsedData.magicOK = (parsedData.magicNumber == expectedMagicWord).all()

        # Check that startIdx is not empty
        if startIdx:

            # Remove the data before the first start index
            if 0 < startIdx[0] < byteBufferLength:
                byteBuffer[:byteBufferLength - startIdx[0]] = byteBuffer[startIdx[0]:byteBufferLength]
                byteBuffer[byteBufferLength - startIdx[0]:] = np.zeros(len(byteBuffer[byteBufferLength - startIdx[0]:]),
                                                                       dtype='uint8')
                byteBufferLength = byteBufferLength - startIdx[0]



            # Check that there have no errors with the byte buffer length
            if byteBufferLength < 0:
                byteBufferLength = 0

            # This code is just outrageously bad, optimised-out
            #--------------------------------------------------
            # # Read the total packet length
            # totalPacketLen = np.matmul(byteBuffer[12:12 + 4], word_4_32)
            # parsedData.frmhdr.totalPacketLen = np.matmul(byteBuffer[12:12 + 4], word_4_32)
            #
            # # Check that all the packet has been read
            # if (byteBufferLength >= totalPacketLen) and (byteBufferLength != 0):
            #     parsedData.magicOK = 1

    # in the "C:\Users\Nathan\guicomposer\runtime\gcruntime.v6\mmWave_Demo_Visualizer\app\mmWave.js",
    # look for "var process1 = function (bytevec)", line 1378


    # Process the message only if the magic word has been found
    if parsedData.magicOK:

        # Initialize the pointer index to the global byteBuffer
        idX = 0

        # Read the header + apply the word
        parsedData.frmhdr.magicNumber = byteBuffer[idX:idX + 8]
        idX += 8

        # parsedData.frmhdr.version = format(np.matmul(byteBuffer[idX:idX + 4], word_4_32), 'x') # looks like "2010004", should be 2.1.4
        # idX += 4

        # REMEMBER: LSB !!!!!
        # SDK Version represented as (MajorNum x 2^24 + MinorNum x 2^16 + BugfixNum x 2^8 + BuildNum)
        parsedData.frmhdr.sdkVersion.BuildNum = np.matmul(byteBuffer[idX:idX + 1], word_4_8)
        idX += 1
        parsedData.frmhdr.sdkVersion.BugfixNum = np.matmul(byteBuffer[idX:idX + 1], word_4_8)
        idX += 1
        parsedData.frmhdr.sdkVersion.MinorNum = np.matmul(byteBuffer[idX:idX + 1], word_4_8)
        idX += 1
        parsedData.frmhdr.sdkVersion.MajorNum = np.matmul(byteBuffer[idX:idX + 1], word_4_8)
        idX += 1



        parsedData.frmhdr.totalPacketLen = np.matmul(byteBuffer[idX:idX + 4], word_4_32)
        idX += 4
        parsedData.frmhdr.platform = format(np.matmul(byteBuffer[idX:idX + 4], word_4_32), 'x') # this is a text looking like "a1443"
        idX += 4
        parsedData.frmhdr.frameNumber = np.matmul(byteBuffer[idX:idX + 4], word_4_32)
        idX += 4
        parsedData.frmhdr.timeCpuCycles = np.matmul(byteBuffer[idX:idX + 4], word_4_32).astype(np.uint32) ## make sure it is understood as UNSIGNED 32 bit
        idX += 4
        parsedData.frmhdr.numDetectedObj = np.matmul(byteBuffer[idX:idX + 4], word_4_32)
        idX += 4
        parsedData.frmhdr.numTLVs = np.matmul(byteBuffer[idX:idX + 4], word_4_32)
        idX += 4

        # save the binary data in the class
        if globals.saveBinaryDebug:
            parsedData.binData = byteBuffer[:parsedData.frmhdr.totalPacketLen]

        ## UNCOMMENT IN CASE OF SDK 2
        #subFrameNumber = np.matmul(byteBuffer[idX:idX+4],word_4_32)
        #idX += 4
        # // subFrame number, uint32
        # if (((Params.platform == mmwInput.Platform.xWR16xx) | | (Params.platform == mmwInput.Platform.xWR18xx)) & & (
        #     Params.tlv_version_uint16 >= 0x0101))

        # Read through all the TLV messages one by one
        for tlvIdx in range(parsedData.frmhdr.numTLVs):

            # Check the header of the TLV message
            tlv_type = np.matmul(byteBuffer[idX:idX + 4], word_4_32)
            idX += 4
            # tlv_length = np.matmul(byteBuffer[idX:idX + 4], word_4_32)
            idX += 4

            # Parse the buffer data differently depending on the TLV message
            if tlv_type == MMWDEMO_UART_MSG_DETECTED_POINTS:

                # list of detected objects, each is
                # typedef volatile struct MmwDemo_detectedObj_t {
                #    uint16_t   rangeIdx;     Range index
                #    uint16_t   dopplerIdx;   Dopler index
                #    uint16_t  peakVal;       Peak value
                #    int16_t  x;              x - coordinate in meters. Q format depends on the range resolution
                #    int16_t  y;              y - coordinate in meters. Q format depends on the range resolution
                #    int16_t  z;              z - coordinate in meters. Q format depends on the range resolution
                # }

                tlv_numObj = np.matmul(byteBuffer[idX:idX + 2], word_4_16)  # TODO: is it the same as "parsedData.frmhdr.numDetectedObj" ?
                idX += 2
                parsedData.tlv_xyzQFormat = 2 ** np.matmul(byteBuffer[idX:idX + 2], word_4_16)
                idX += 2

                for objectNum in range(tlv_numObj):
                    if (objectNum <= globals.nbrStoredEchoesInClass-1):  # limit the detected object list to the size we have allocated

                        # Read the data for each object

                        parsedData.objList[objectNum].echoNumber = objectNum # personal counter for integrity check
                        ## no increment here because we didn't parse
                        parsedData.objList[objectNum].rangeIdx = np.matmul(byteBuffer[idX:idX + 2], word_4_16)
                        idX += 2
                        parsedData.objList[objectNum].dopplerIdx = np.matmul(byteBuffer[idX:idX + 2], word_4_16)
                        idX += 2
                        parsedData.objList[objectNum].peakVal = np.matmul(byteBuffer[idX:idX + 2], word_4_16)
                        idX += 2
                        parsedData.objList[objectNum].x = np.matmul(byteBuffer[idX:idX + 2], word_4_16)
                        idX += 2
                        parsedData.objList[objectNum].y = np.matmul(byteBuffer[idX:idX + 2], word_4_16)
                        idX += 2
                        parsedData.objList[objectNum].z = np.matmul(byteBuffer[idX:idX + 2], word_4_16)
                        idX += 2
                        parsedData.objList[objectNum].isValid = True  # indicates that this object can be used later in post-processing

                        # the corrections on the retrieved values are applied later in the function called "postprocessData14xx"

                parsedData.dataOK = True

        # Remove already processed data
        if idX > 0 and byteBufferLength > idX:
            shiftSize = parsedData.frmhdr.totalPacketLen

            byteBuffer[:byteBufferLength - shiftSize] = byteBuffer[shiftSize:byteBufferLength]
            byteBuffer[byteBufferLength - shiftSize:] = np.zeros(len(byteBuffer[byteBufferLength - shiftSize:]),
                                                                 dtype='uint8')
            byteBufferLength = byteBufferLength - shiftSize

            # Check that there are no errors with the buffer length
            if byteBufferLength < 0:
                byteBufferLength = 0

    return parsedData
    ## END OF FUNCTION
#***********************************************************************************************************************

#***********************************************************************************************************************
def stopLogger(loggerObject):
    ### delete all the loggers

    handlers = loggerObject.handlers

    for handler in handlers:
        handler.close()
        loggerObject.removeHandler(handler)

    return True
    ## END OF FUNCTION
#***********************************************************************************************************************

#***********************************************************************************************************************
def listSerialports():
    # Find and return a list of all EiBotBoard units
    # connected via USB port.

    # check platform
    CurrentOS = platform.system()
    if (CurrentOS == 'Windows' or CurrentOS == 'win32'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif CurrentOS == 'Linux':
        ## this might be problematic if the user uses a linux platform for DEBUG
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    else:
        print("Operating system not supported")
        # raise EnvironmentError('Unsupported platform')
        return False
        # 'win32'   for Windows(Win32)
        # 'cygwin'  for Windows(cygwin)
        # 'darwin'  for macOS
        # 'aix'     for AIX


    #init
    result = []
    # loop on the available serial ports and open and close them to check
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass

    if globals.debugPrint:
        print(result)

    return result

    ## END OF FUNCTION
#***********************************************************************************************************************

#***********************************************************************************************************************
def checkRadarSerialPort(serialNameCFG, serialNameDATA):
    ## Check the radar USB cable is plugged in and accessible

    # Get the list of available serial port
    if globals.debugPrint:
        print(listSerialports())

    # Check there is at least 2 usable serial ports
    if (len(listSerialports()) >= 0): # TODO Should be 2

        ## check that DATAserial and CFGserial are different
        if (True): # TODO Should be "serialNameCFG != serialNameDATA"

            # Check if the serial port that was in the logger config.ini file can be found in the list of available serial port

            # Check the config serial port 1st
            CFGserialGood = serialNameCFG in listSerialports()
            print("CFGserialGood?: {}".format(CFGserialGood))

            # Check the data serial port 2nd
            DATAserialGood = serialNameDATA in listSerialports()
            print("DATAserialGood?: {} ".format(DATAserialGood))

            print("Both serial ports good?: {}".format(CFGserialGood and DATAserialGood))

            return (CFGserialGood and DATAserialGood)

        else:
            print("The 2 serial port provided for the radar are the same BUT should be DIFFERENT")
            return False

    else:
        print("Not enough available serial ports, at least 2 needed: {} available".format(len(listSerialports())))
        return False


    ## END OF FUNCTION
#***********************************************************************************************************************

#***********************************************************************************************************************
def checkUSBDrivePresent(usbDriveName):
    ### Check the USB drive is plugged in on the RPi so we can save the data there

    print("Checking the USB drive is plugged on the RPi")

    ## https://stackoverflow.com/questions/4553129/when-to-use-os-name-sys-platform-or-platform-system
    ## The output of sys.platform and os.name are determined at compile time. platform.system() determines the system type at run time.
    CurrentOS = platform.system()


    if (CurrentOS == 'Windows' or CurrentOS == 'win32'):
        return True, ""
    elif CurrentOS == 'Linux':

        # init
        usbPresent = False
        usbName = ""

        ## this might be problematic if the user uses a linux platform for DEBUG
        # Step 1/3 check the USB devices, there should be one from the USB drive manufacturer
        print("What are the USB device connected to the pi?")
        shellAnswer = subprocess.run(['lsusb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Data out: \r\n{}".format(shellAnswer.stdout.decode()))
        print("Any error?: {}".format(shellAnswer.stderr.decode()))

        if ( len(shellAnswer.stdout.decode()) > 0 and shellAnswer.stderr.decode()=="" ):

            # Step 1/3 check the devices, there should be a sda1
            # ls /dev/sd*
            # /dev/sda  /dev/sda1
            print("Is there a device connected to the pi?")
            # With the next command, I cannot do: ls /dev/sd*
            #       ls: cannot access '/dev/sd*': No such file or directory
            #       shellAnswer = "/dev/sdb\n/dev/sda1\n/dev/ddaf\n/dev/sda2\n/dev/pthb\n/dev/sda50\n"
            # usbDriveName = "sda1"
            shellAnswer = executeShellAsSudo('ls /dev')
            # print("Data out: {}".format(shellAnswer))
            shellAnswer = shellAnswer.splitlines()  # from string to list, cut on "\n"
            # using list comprehension to get string with substring
            res = [i for i in shellAnswer if usbDriveName in i]
            print("Any {} in the list?: {},{}".format(usbDriveName, len(res), res))

            # sdOccurencesIndx = [m.start() for m in re.finditer('sd', shellAnswer)]
            # sdOccurencesTxt = [shellAnswer[m:m + 4] for m in sdOccurencesIndx]
            # print("Any sd* in the list?: {},{}, {}".format(len(sdOccurencesIndx), sdOccurencesIndx, sdOccurencesTxt))

            if (len(res) == 1):

                # Step 3/3 check the media folder (if the USB drive has been mounted), there should be a volume name
                # ls /media/pi
                print("Is there a mounted volume connected to the pi?")
                shellAnswer = executeShellAsSudo('ls /media/pi')
                print("Data out: {}".format(shellAnswer))

                if (shellAnswer != ""):
                    usbPresent = True
                    usbName = shellAnswer

        return usbPresent, usbName

    else:
        print("Operating system not supported")
        # 'win32'   for Windows(Win32)
        # 'cygwin'  for Windows(cygwin)
        # 'darwin'  for macOS
        # 'aix'     for AIX
        return False
    ## END OF FUNCTION
#***********************************************************************************************************************

#***********************************************************************************************************************
def checkStartFiles():
    ### run the checks of all the files
    return (checkLoggerParameters() and checkRadarParameters())
    ## END OF FUNCTION
#***********************************************************************************************************************

#***********************************************************************************************************************
def checkLoggerParameters():
    ### Check the parameters.ini file is present (contain the python code parameters)


    #global LoggerParametersFolderName, LoggerParametersFileName

    print("Checking Logger Parameters file")
    # first check the folder
    if os.path.isdir(os.getcwd() + globals.pathSeparator + globals.LoggerParametersFolderName):
        print("LoggerParameters FOLDER present")
        # then check the file
        if os.path.isfile(os.getcwd() + globals.pathSeparator + globals.LoggerParametersFolderName + globals.pathSeparator + globals.LoggerParametersFileName):
            print("LoggerParameters FILE present")
            print("Logger: ALL GOOD")
            return True

    else:
        # No folder
        return False
    ## END OF FUNCTION
#***********************************************************************************************************************

#***********************************************************************************************************************
def checkRadarParameters():
    ### Check the radar parameter file (.cfg) is present (contain the data to be send via UART)

    # global RadarParametersFolderName, RadarParametersFileName

    print("Checking Radar Parameters file")
    # first check the folder
    if os.path.isdir(os.getcwd() + globals.pathSeparator + globals.RadarParametersFolderName):
        print("RadarParameters FOLDER present")
        # then check the file
        if os.path.isfile(os.getcwd() + globals.pathSeparator + globals.RadarParametersFolderName + globals.pathSeparator + globals.RadarParametersFileName):
            print("RadarParameters FILE present")
            print("Radar: ALL GOOD")
            return True
    else:
        # No folder
        return False
    ## END OF FUNCTION
# ***********************************************************************************************************************

#***********************************************************************************************************************
def readLoggerParameters():
    ### parse the logger .ini file

    print("Reading the Logger Parameters file")

    ## create an empty dictionary
    # Python3 code to demonstrate use of
    # {} symbol to initialize dictionary
    loggerParametersDict = {}

    # # print dictionary
    # print(loggerParametersDict)
    #
    # # print length of dictionary
    # print("Dictionary length:", len(loggerParametersDict))
    #
    # # print type
    # print(type(loggerParametersDict))


    ## instantiate the ini file parser
    config = configparser.ConfigParser()
    # give the name and path of the file

    config.read(globals.LoggerParametersFolderName + globals.pathSeparator + globals.LoggerParametersFileName)


    ## Debug only TODO: remove
    ## print the list of all section in the ini file
    # print(config.sections())

    # as a dictionary
    paramDict = {s:dict(config.items(s)) for s in config.sections()}

    # [Check]
    fileGood = int(paramDict["Check"]["filegood"])

    ## Check fileGood in the ini file
    if 'fileGood' in locals():
        if fileGood == 1:
            print("Final marker on logger INI config file FOUND with GOOD value")
            return paramDict
        else:
            print("Final marker on logger INI config file has BAD value")
            return False
    else:
        print("Final marker on logger INI config file NOT found")
        return False

    ## END OF FUNCTION
#***********************************************************************************************************************


#***********************************************************************************************************************
def radarStop(serialPort):
    # Function to send a stop command to the radar

    #init
    sendOK = True

    command = "sensorStop"
    serialPort.write((command + '\n').encode())

    # Wait a bit so the radar will have the time to reply with multiple messages
    time.sleep(1.0)

    # init
    reply = []
    joined_seq = ""
    count = 1
    radarOk = False

    while serialPort.in_waiting:
        for c in serialPort.readline():
            if chr(c) == '\n':

                # Convert a list of characters into a string
                reply = "".join(reply)

                print("Radar replied (line " + str(count) + "): " + joined_seq)

                ## Check if the radar replied with "ok" (be handling it one byte at a time)
                radarOk = radarOk or ("Done" in reply)

                # reset
                reply = []
                count += 1
                # break
                time.sleep(0.5)
            else:
                # if the char is not a terminator
                reply.append(chr(c))  # convert from ANSII
                joined_seq = ''.join(str(v) for v in reply)  # Make a string from array

        # end of the while, check if "Done" has been received

    if radarOk:
        print("Command accepted by the radar")
    else:
        print("Problem! Command rejected by the radar")

    ## add the current bolean state to the global one
    sendOK = sendOK and radarOk

    return sendOK

   ## END OF FUNCTION
#***********************************************************************************************************************

#***********************************************************************************************************************
def radarStart(serialPort):
    # Function to send a start command to the radar

    #init
    sendOK = True

    command = "sensorStart"
    serialPort.write((command + '\n').encode())

    # Wait a bit so the radar will have the time to reply with multiple messages
    time.sleep(1.0)

    # init
    reply = []
    joined_seq = ""
    count = 1
    radarOk = False

    while serialPort.in_waiting:
        for c in serialPort.readline():
            if chr(c) == '\n':

                # Convert a list of characters into a string
                reply = "".join(reply)

                print("Radar replied (line " + str(count) + "): " + joined_seq)

                ## Check if the radar replied with "ok" (be handling it one byte at a time)
                radarOk = radarOk or ("Done" in reply)

                # reset
                reply = []
                count += 1
                # break
                time.sleep(0.5)
            else:
                # if the char is not a terminator
                reply.append(chr(c))  # convert from ANSII
                joined_seq = ''.join(str(v) for v in reply)  # Make a string from array

        # end of the while, check if "Done" has been received

    if radarOk:
        print("Command accepted by the radar")
    else:
        print("Problem! Command rejected by the radar")

    ## add the current bolean state to the global one
    sendOK = sendOK and radarOk

    return sendOK

   ## END OF FUNCTION
#***********************************************************************************************************************

#***********************************************************************************************************************
def serialSendConfigToRadar(configFileName, serialPort):
    # Function to send the configuration from
    # the radar configuration file (.CFG) to the radar via configuration serial

    #init
    sendOK = True

    print("-" * 50)

    ## Send a 'enter key' to make the header "mmwDemo:/>" appear
    serialPort.write(('\n').encode())

    # Wait a bit so the radar will have the time to reply with multiple messages
    time.sleep(1.0)


    # Read the radar configuration file and send each line to the radar via serial
    config = [line.rstrip('\r\n') for line in open(configFileName)]
    for command in config:

        print("Retrieved command from file: {}".format(command))

        ## Check if the line is a comment or not
        if not(command.startswith('%')):
            print("Sending to radar: {}".format(command))
            serialPort.write((command + '\n').encode())

            # Wait a bit so the radar will have the time to reply with multiple messages
            time.sleep(0.1) # TODO: make smaller

            # init
            reply = []
            joined_seq = ""
            count = 1
            radarOk = False

            while serialPort.in_waiting:
                for c in serialPort.readline():
                    if chr(c) == '\n':

                        # Convert a list of characters into a string
                        reply = "".join(reply)

                        print("Radar replied (line " + str(count) + "): " + joined_seq)

                        ## Check if the radar replied with "ok" (be handling it one byte at a time)
                        radarOk = radarOk or ("Done" in reply)

                        # reset
                        reply = []
                        count += 1
                        # break
                        time.sleep(0.1)
                    else:
                        # if the char is not a terminator
                        reply.append(chr(c))  # convert from ANSII
                        joined_seq = ''.join(str(v) for v in reply)  # Make a string from array

                # end of the while, check if "Done" has been received

            if radarOk:
                print("Command accepted by the radar")
            else:
                print("Problem! Command rejected by the radar")

            ## add the current bolean state to the global one
            sendOK = sendOK and radarOk

            ## wait a bit between 2 messages so that the radar UART buffer does not overflow
            time.sleep(0.1)

    print("-" * 50)

    return sendOK

   ## END OF FUNCTION
#***********************************************************************************************************************

#***********************************************************************************************************************
def parseConfigFile(configFileName):
    # Function to parse the data inside the configuration file
    # Saultes45 (Shamelessly taken from Gorordo's code)

    configParameters = {}  # Initialize an empty dictionary to store the configuration parameters

    # Read the configuration file and send it to the board
    config = [line.rstrip('\r\n') for line in open(configFileName)]
    for i in config:

        # Split the line
        splitWords = i.split(" ")

        # Hardcode the number of antennas, change if other configuration is used
        numRxAnt = 4
        numTxAnt = 2

        # Get the information about the profile configuration
        if "profileCfg" in splitWords[0]:
            startFreq = int(float(splitWords[2]))
            idleTime = int(splitWords[3])
            rampEndTime = float(splitWords[5])
            freqSlopeConst = float(splitWords[8])
            numAdcSamples = int(splitWords[10])
            numAdcSamplesRoundTo2 = 1  # Saultes45: trailing semicolon removed

            while numAdcSamples > numAdcSamplesRoundTo2:
                numAdcSamplesRoundTo2 = numAdcSamplesRoundTo2 * 2  # Saultes45: trailing semicolon removed

            digOutSampleRate = int(splitWords[11])  # Saultes45: trailing semicolon removed

        # Get the information about the frame configuration
        elif "frameCfg" in splitWords[0]:

            chirpStartIdx = int(splitWords[1])  # Saultes45: trailing semicolon removed
            chirpEndIdx = int(splitWords[2])   # Saultes45: trailing semicolon removed
            numLoops = int(splitWords[3])   # Saultes45: trailing semicolon removed
            numFrames = int(splitWords[4])   # Saultes45: trailing semicolon removed
            #framePeriodicity = int(splitWords[5]);
            framePeriodicity = float(splitWords[5]) # corrected by Saultes45 on 2022-05-05 fo allow for 30fs (int->float)

    # Combine the read data to obtain the configuration parameters
    numChirpsPerFrame = (chirpEndIdx - chirpStartIdx + 1) * numLoops
    configParameters["numDopplerBins"] = numChirpsPerFrame / numTxAnt
    configParameters["numRangeBins"] = numAdcSamplesRoundTo2
    configParameters["rangeResolutionMeters"] = (3e8 * digOutSampleRate * 1e3) / (
                2 * freqSlopeConst * 1e12 * numAdcSamples)
    configParameters["rangeIdxToMeters"] = (3e8 * digOutSampleRate * 1e3) / (
                2 * freqSlopeConst * 1e12 * configParameters["numRangeBins"])
    configParameters["dopplerResolutionMps"] = 3e8 / (
                2 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * configParameters["numDopplerBins"] * numTxAnt)
    configParameters["maxRange"] = (300 * 0.9 * digOutSampleRate) / (2 * freqSlopeConst * 1e3)
    configParameters["maxVelocity"] = 3e8 / (4 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * numTxAnt)

    return configParameters
   ## END OF FUNCTION
#***********************************************************************************************************************



#***********************************************************************************************************************
def main():


    ## step 0: initialisation
    ##-----------------------

    # Create a reference number which is shared for all the data generated for this particular execution
    # This reference is just the date time
    testRef = time.strftime(globals.logFileNameDateFormat)

    displayDebugData(testRef)


    # initialise all the booleans
    envOK = True

    # Path
    CurrentOS = platform.system()
    if (CurrentOS == 'Windows' or CurrentOS == 'win32'):
        globals.pathSeparator = globals.pathSeparator_Win
    elif CurrentOS == 'Linux':
        globals.pathSeparator = globals.pathSeparator_Rpi
    else:
        # Unknown OS
        raise BadOS
        # break
    print("Parsing done")


    ## step 1: check the necessary files are present on the system before we start
    ##-----------------------------------------------------------------------------


    ## step1.1: config files
    ##-----------------------

    if checkStartFiles():
        print("All necessary files present")

        ## Since the config files are present, get the logger parameters
        loggerParametersDict = readLoggerParameters()

        # Store it as individual variables
        # Careful about the uppercase!!

        # [USB drive]
        # driveName = sda1
        driveName = loggerParametersDict["USB drive"]["drivename"]

        # [Logger]
        nbrLogFiles = int(loggerParametersDict["Logger"]["nbrlogfiles"])
        dataFolderName = loggerParametersDict["Logger"]["datafoldername"]
        logMode = loggerParametersDict["Logger"]["logmode"]

        if loggerParametersDict["Logger"]["logencoding"] == "None":
            logencoding = None
        else:
            logencoding = loggerParametersDict["Logger"]["logencoding"]

        maxLogFileMegaBytesSize = int(loggerParametersDict["Logger"]["maxlogfilemegabytessize"])
        logDelay = int(loggerParametersDict["Logger"]["logdelay"])

        # [Radar]

        serialConfigName_RPi = loggerParametersDict["Radar"]["serialconfigname_rpi"]
        serialConfigName_Win = loggerParametersDict["Radar"]["serialconfigname_win"]
        serialConfigBaud = int(loggerParametersDict["Radar"]["serialconfigbaud"])
        serialDataName_RPi = loggerParametersDict["Radar"]["serialdataname_rpi"]
        serialDataName_Win = loggerParametersDict["Radar"]["serialdataname_win"]
        serialDataBaud = int(loggerParametersDict["Radar"]["serialdatabaud"])
        radarPlatform = loggerParametersDict["Radar"]["radarplatform"]
        radarSDKVersion = loggerParametersDict["Radar"]["radarsdkversion"]
        serialTimeout = float(loggerParametersDict["Radar"]["serialtimeout"])
        # radarMagicHeader_hex = "0201040306050807"
        # OBJ_STRUCT_SIZE_BYTES = 12;
        # BYTE_VEC_ACC_MAX_SIZE = 2 ** 15;
        # MMWDEMO_UART_MSG_DETECTED_POINTS = 1;
        # MMWDEMO_UART_MSG_RANGE_PROFILE = 2;
        # maxBufferSize = 2 ** 15;
        # magicWord = [2, 1, 4, 3, 6, 5, 8, 7]

    else:
        ## let the user know an error occurred
        envOK = (envOK and False) # add to the error
        # print("Number of frames logged (num_logged_frames): {}".format(num_logged_frames))
        print(globals.crashMarker)
        print("Main code stopped because the necessary files are NOT present on the system")

    print("-" * 50)

    ## step1.2: USB drive
    ##-----------------------

    # The function will make the distinction between the OS it is executed on
    USBOK, USBName = checkUSBDrivePresent("sda1")
    if USBOK:
        print("USB drive is present and accessible")
    else:
        ## let the user know an error occurred
        envOK = (envOK and False)  # add to the error
        # print("Number of frames logged (num_logged_frames): {}".format(num_logged_frames))
        print(globals.crashMarker)
        print("Main code stopped because the USB drive is not connected or recognised by the system")
        raise USBNotRecognised

    print("-" * 50)

    ## step1.3: Serial ports
    ##-----------------------

    CurrentOS = platform.system()
    if (CurrentOS == 'Windows' or CurrentOS == 'win32'):
        if checkRadarSerialPort(serialConfigName_Win, serialDataName_Win):
            print("Both radar serial ports are present and accessible")
        else:
            ## let the user know an error occurred
            envOK = (envOK and False)  # add to the error
            # print("Number of frames logged (num_logged_frames): {}".format(num_logged_frames))
            print(globals.crashMarker)
            print(
                "Main code stopped because one or multiple serial ports are NOT present, did you plug + power the radar?")
    elif CurrentOS == 'Linux':
        if checkRadarSerialPort(serialConfigName_RPi, serialDataName_RPi):
            print("Both radar serial ports are present and accessible")
        else:
            ## let the user know an error occurred
            envOK = (envOK and False)  # add to the error
            # print("Number of frames logged (num_logged_frames): {}".format(num_logged_frames))
            print(globals.crashMarker)
            print(
                "Main code stopped because one or multiple serial ports are NOT present, did you plug + power the radar?")
    else:
        # Unknown OS
        raise BadOS

    print("-" * 50)






    if envOK:

        print("All systems checked, code continues")

        ## step2.1: Read and parse the data from the radar config file
        ##--------------------------------------------------------------


        print("Parsing the radar configuration")
        # Get the configuration parameters from the configuration file (from Gorordo's code)
        configParameters = parseConfigFile(globals.RadarParametersFolderName + globals.pathSeparator + globals.RadarParametersFileName)

        print("Parsing done")
        print("-" * 50)



        ## step2.2: Prepare the data-logging
        ##-----------------------------------

        # Check the path exists

        print("Preparing datalogging")

        CurrentOS = platform.system()
        if (CurrentOS == 'Windows' or CurrentOS == 'win32'):
            print("Since we are on Windows, we put the data in the same folder as the code")
            # Put the data folder in root/CWD
            startPath = os.getcwd()

        elif CurrentOS == 'Linux':
            print("Since we are on the Raspberry Pi, we put the data in the USB drive")
            # Put the data folder in the USB drive
            startPath = "/media/pi/" + USBName.rstrip()


        else:
            # Unknown OS
            raise BadOS
            startPath = ''


        # Create the root folder for the sub folders
        if not (os.path.isdir(startPath + globals.pathSeparator + dataFolderName)):
            os.mkdir(startPath + globals.pathSeparator + dataFolderName)

        # In this data folder, create a subfolder for this execution
        if not (
                os.path.isdir(
                                    startPath + globals.pathSeparator + dataFolderName + globals.pathSeparator + testRef)):
            os.mkdir(startPath + globals.pathSeparator + dataFolderName + globals.pathSeparator + testRef)

        # Generate a log file name
        logFileName = \
            startPath + globals.pathSeparator +\
            dataFolderName + globals.pathSeparator +\
            testRef + globals.pathSeparator +\
            testRef + '-Data.log'





        print("Preparing logger")
        # Prepare the logger
        log = logging.getLogger()
        log.setLevel(logging.DEBUG)
        logFileHandler = RotatingFileHandler(filename=logFileName,
                                             mode=logMode,
                                             backupCount=nbrLogFiles - 1,
                                             maxBytes=maxLogFileMegaBytesSize * 1024 * 1024, # conv. from byte to MB
                                             encoding=logencoding,
                                             delay=logDelay)
        logFileHandler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            fmt=globals.lineLogFormat,
            datefmt=globals.timeStampDateFormat
        )

        logFileHandler.setFormatter(formatter)
        log.addHandler(logFileHandler)

        # Add a header to the log file (Notice the space at the start)
        log.info(globals.logFileHeader)

        ## step3: Open the radar DATA serial port in preparation of receiving the data
        ##-----------------------------------------------------------------------------

        try:
            CurrentOS = platform.system()
            if (CurrentOS == 'Windows' or CurrentOS == 'win32'):
                radarDataSerialPort = serial.Serial(
                    port=serialDataName_Win,
                    baudrate=serialDataBaud,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=serialTimeout
                )

            elif CurrentOS == 'Linux':
                radarDataSerialPort = serial.Serial(
                    port=serialDataName_RPi,
                    baudrate=serialDataBaud,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=serialTimeout
                )

            else:
                # Unknown OS
                print("Unsupported OS")


            radarDataSerialPort.rtscts = 0

        except Exception as e:  # as e syntax added in ~python2.5
            print("Error while trying to open the radar DATA serial port")
            raise e


        if radarDataSerialPort.isOpen():
            print("radar DATA serial port is open")
        else:
            print("Despite earlier checks, radar DATA port could not be opened, aborting")





        ## step4: Send the configuration to the radar via UART
        ##-----------------------------------------------------


        ## Configure the radar to get the data we want
        try:

            CurrentOS = platform.system()
            if (CurrentOS == 'Windows' or CurrentOS == 'win32'):
                radarConfigSerialPort = serial.Serial(
                    port=serialConfigName_Win,
                    baudrate=serialConfigBaud,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=serialTimeout
                )

            elif CurrentOS == 'Linux':
                radarConfigSerialPort = serial.Serial(
                    port=serialConfigName_RPi,
                    baudrate=serialConfigBaud,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=serialTimeout
                )

            else:
                # Unknown OS
                print("Unsupported OS")

            radarConfigSerialPort.rtscts = 0

        except Exception as e:  # as e syntax added in ~python2.5
            print("Error while trying to open the radar CONFIG serial port")
            raise e


        if radarConfigSerialPort.isOpen():
            print("radar CONFIG serial port is open")
        else:
            print("Despite earlier checks, radar CONFIG port could not be opened, aborting")

        startEllapsedTime = time.time()
        if globals.radarAlreadyConfigured:
            confSent2Radar = radarStart(radarConfigSerialPort)
        else:
            confSent2Radar = serialSendConfigToRadar(globals.RadarParametersFolderName +
                                                     globals.pathSeparator +
                                                     globals.RadarParametersFileName,
                                                     radarConfigSerialPort)
        print("Time elapsed for sending configuration: {:5.1f}".format(time.time() - startEllapsedTime))
        del startEllapsedTime

        globals.radarAlreadyConfigured = True
        print("Good configuration?: {}".format(confSent2Radar))

        # close the serial port
        if radarConfigSerialPort.isOpen():
            radarConfigSerialPort.close()
            print("Radar CONFIG serial has been closed")



        # Aquisition loop
        # ---------------

        print("-"*50)
        print("Starting aquisition")

        # Making sure we are not trying to display more echoes than actually storing
        globals.nbrEchosDisplayed = min(globals.nbrEchosDisplayed, globals.nbrStoredEchoesInClass)
        print("Logging only {} echoes on maximum {}".format(globals.nbrEchosDisplayed, globals.nbrStoredEchoesInClass))

        # Statistics variables initialisation (to display in the console when user close the GUI)
        num_logged_frames = 0
        start_time = time.time()

        for cnt in range(globals.nbrAquisitionLoops):
            try:
                print("Frame #: {}".format(num_logged_frames))
                radarClass = readAndParseData14xx(radarDataSerialPort)

                # Only post-process if the received frame is valid
                if radarClass.dataOK:
                    radarClass = postprocessData14xx(radarClass, configParameters) ## TODO: in that function, only get the echoes that are within a range (distance) + velocity + angle (straight down)
                    # For the conversion check, just look at the first object
                    if radarClass.objList[0].isConverted:

                        # At every iteration, do the following
                        time_ms = round((time.time() - start_time) * 1000)  # conversion from [ms] to [s]

                        # Add the header to the finalFrame
                        finalFrame = globals.headerFormat.format(
                            time_ms,
                            radarClass.frmhdr.magicNumber,
                            #radarClass.frmhdr.version,
                            radarClass.frmhdr.sdkVersion.MajorNum,
                            radarClass.frmhdr.sdkVersion.MinorNum,
                            radarClass.frmhdr.sdkVersion.BugfixNum,
                            radarClass.frmhdr.sdkVersion.BuildNum,
                            radarClass.frmhdr.totalPacketLen,
                            radarClass.frmhdr.platform,
                            radarClass.frmhdr.frameNumber,
                            radarClass.frmhdr.timeCpuCycles,
                            radarClass.frmhdr.numDetectedObj,
                            radarClass.frmhdr.numTLVs,
                            radarClass.tlv_xyzQFormat)  # init

                        # Add the echoes, one by one, to the finalFrame
                        for cnt_echo in range(globals.nbrEchosDisplayed):
                            finalFrame = finalFrame + globals.echoSeparator + globals.singleEchoFormat.format(
                                cnt_echo,
                                radarClass.objList[cnt_echo].echoNumber,
                                radarClass.objList[cnt_echo].isValid,
                                radarClass.objList[cnt_echo].isConverted,
                                radarClass.objList[cnt_echo].x,
                                radarClass.objList[cnt_echo].y,
                                radarClass.objList[cnt_echo].z,
                                radarClass.objList[cnt_echo].dopplerVal,
                                radarClass.objList[cnt_echo].velocity,
                                radarClass.objList[cnt_echo].rangeIdx,
                                radarClass.objList[cnt_echo].rangeVal,
                                radarClass.objList[cnt_echo].dopplerIdx,
                                radarClass.objList[cnt_echo].peakVal,
                                radarClass.objList[cnt_echo].elv,
                                radarClass.objList[cnt_echo].azmth)

                        log.info(finalFrame)
                        num_logged_frames = num_logged_frames + 1  # Increment the frame counter

                    time.sleep(globals.loopSleepTimeSeconds)  # Wait here so have the new data in the RPi USB buffer

            # Stop the program and close everything if Ctrl + c is pressed on the keyboard
            except KeyboardInterrupt:
                break

        print("Data aquisition loop done")
        print("-" * 50)

        # End of aquisition loop
        # ---------------------

        # close the DATA serial port
        if radarDataSerialPort.isOpen():
            radarDataSerialPort.close()
            print("Radar CONFIG serial has been closed")

        # stop the logger object
        stopLogger(log)
        del log


        if globals.saveBinaryDebug:
            # for debug purpose ONLY, save binary data
            rawBinFileName = os.getcwd() + globals.pathSeparator + dataFolderName + globals.pathSeparator + testRef + globals.pathSeparator + testRef + '-Raw.bin'
            file = open(rawBinFileName, "wb")
            file.write(radarClass.binData)
            file.close()

        # while True:
        #     try:
        #
        #     # Stop the program and close everything if Ctrl + c is pressed on the keyboard
        #     except KeyboardInterrupt:
        #         break





        # Send a stop command to the radar via the CFG serial port
        try:

            CurrentOS = platform.system()
            if (CurrentOS == 'Windows' or CurrentOS == 'win32'):
                radarConfigSerialPort = serial.Serial(
                    port=serialConfigName_Win,
                    baudrate=serialConfigBaud,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=serialTimeout
                )

            elif CurrentOS == 'Linux':
                radarConfigSerialPort = serial.Serial(
                    port=serialConfigName_RPi,
                    baudrate=serialConfigBaud,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=serialTimeout
                )

            else:
                # Unknown OS
                print("Unsupported OS")

            radarConfigSerialPort.rtscts = 0

        except Exception as e:
            print("Error while trying to open the radar CONFIG serial port")
            raise e

        if radarConfigSerialPort.isOpen():
            print("radar CONFIG serial port is open")
        else:
            print("Despite earlier checks, radar CONFIG port could not be opened, aborting")

        stopSent2Radar = radarStop(radarConfigSerialPort)
        print("Stop command worked?: {}".format(stopSent2Radar))

        # close the CONFIG serial port
        if radarConfigSerialPort.isOpen():
            radarConfigSerialPort.close()
            print("Radar config serial is now closed")

        print("-" * 50)
        print("END OF THE SCRIPT")
        print("#" * 50)

    else:
        print("Aborted due to environment errors")
        print("#"*50)
## END OF FUNCTION
# ***********************************************************************************************************************


# -------------------------    MAIN   -----------------------------------------


# This is where we execute the main
if __name__ == "__main__":
    main()

## END OF FILE
##&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&





    # from: R:\mmwave_industrial_toolbox_4_11_0\labs\People_Counting\visualizer

    # decode IFDM point Cloud TLV
    # def parseDetectedObjectsIFDM(self, data, tlvLength):
    #     pUnitStruct = '4f'
    #     pUnitSize = struct.calcsize(pUnitStruct)
    #     pUnit = struct.unpack(pUnitStruct, data[:pUnitSize])
    #     data = data[pUnitSize:]
    #     objStruct = '2B2h'
    #     objSize = struct.calcsize(objStruct)
    #     self.numDetectedObj = int((tlvLength - 16) / objSize)
    #     # print('Parsed Points: ', self.numDetectedObj)
    #     for i in range(self.numDetectedObj):
    #         try:
    #             az, doppler, ran, snr = struct.unpack(objStruct, data[:objSize])
    #             data = data[objSize:]
    #             # get range, azimuth, doppler, snr
    #             self.pcPolar[0, i] = ran * pUnit[2]  # range
    #             if (az >= 128):
    #                 az -= 256
    #             self.pcPolar[1, i] = math.radians(az * pUnit[0])  # azimuth
    #             self.pcPolar[2, i] = doppler * pUnit[1]  # doppler
    #             self.pcPolar[3, i] = snr * pUnit[3]  # snr
    #
    #             # Sense and direct format
    #             # [frame #][header,pt cloud data,target info]
    #             # [][header][magic, version, platform, timestamp, packetLength, frameNum, subFrameNum, chirpMargin, frameMargin, uartSentTime, trackProcessTime, numTLVs, checksum]
    #             # [][pt cloud][pt index][#range, azim, doppler, snr]
    #             # [][target][Target #][TID,x,y,vx,vy,ax,ay]
    #             self.textStruct2D[self.frameNum % 1000, 1, i, 0] = self.pcPolar[0, i]  # range
    #             self.textStruct2D[self.frameNum % 1000, 1, i, 1] = self.pcPolar[1, i]  # az
    #             self.textStruct2D[self.frameNum % 1000, 1, i, 2] = self.pcPolar[2, i]  # doppler
    #             self.textStruct2D[self.frameNum % 1000, 1, i, 3] = self.pcPolar[3, i]  # snr
    #
    #         except:
    #             self.numDetectedObj = i
    #             break
    #     self.polar2Cart()


