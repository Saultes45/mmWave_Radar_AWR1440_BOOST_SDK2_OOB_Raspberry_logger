#!/usr/bin/env python3


# This file contains all the global variables used in the main python code: 'logRadar.py'

# -------------------Metadata----------------------
# Creator: Nathanael ESNAULT

# nathanael.esnault@gmail.com
# or
# nesn277@aucklanduni.ac.nz

# Creation date 2022-05-13
# Version	1.0

# Version Control: https://github.com/Saultes45/

# ---------------------- global variables []------------------

## Debug
##-------

# Chose if we have to send the config parameters to the radar
radarAlreadyConfigured = False

# Chose if we save the binary data of the last TLV message
saveBinaryDebug = False

# Debug parameters: must be global
debugPrint = True

## Configuration files
##---------------------

# Name of file and path for the logger configuration (cannot be put in the configuration file for obvious reasons)
LoggerParametersFolderName  = "01_LoggerParameters"
LoggerParametersFileName    = "Parameter.ini"

# Name of file and path for the radar configuration (cannot be put in the configuration file for obvious reasons)
RadarParametersFolderName   = "02_RadarParameters"
RadarParametersFileName     = "1443config_8Hz.cfg"


## Datalogging
##------------

# Path:
#   Windows: backslash \
#   Linux: standard slash /
pathSeparator_Win = "\\"
pathSeparator_Rpi = "/"
pathSeparator = ""  # initialised to nothing, will be filled by main()

# The following variables could not be put in the logger .ini file because of their format
lineLogFormat           = '%(asctime)s.%(msecs)03d%(message)s'  # Comma without space between timestamp field and message field is not supported
logFileNameDateFormat   = '%Y-%m-%d--%H-%M-%S'
timeStampDateFormat     = '%Y-%m-%d_%H-%M-%S'

# ## Not here because of numpy
# byteBuffer = np.zeros(2**15, dtype='uint8')
# byteBufferLength = 0

## Aquisition
##-------------

nbrAquisitionLoops      = 20
nbrStoredEchoesInClass  = 10
nbrEchosDisplayed       = 10  # make sure this number is >= the number of echoes in class
loopSleepTimeSeconds    = 0.120  # Sampling frequency of 8Hz (same as pressure senors), 0.125 actually needed

crashMarker = "--------- /!\ CRASH /!\ ---------"

## Display format
##----------------

headerFormat = ",{},{},{:02d},{:02d},{:02d},{:02d},{},{},{:010d},{:011d},{:02d},{},{:.2f}"
singleEchoFormat = "{:02d},{:02d},{},{},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f},{:04d},{:.5f},{:04d},{:.5f},{:.5f},{:.5f}"
echoSeparator = "\t"

logFileHeader = " Aquisition Time[ms]," \
				" Magic Number[N/A]," \
				" Version-Major[N/A]," \
                " Version-Minor[N/A]," \
                " Version-BugFix[N/A]," \
                " Version-Build[N/A]," \
				" Total Packet Length[bytes]," \
				" Platform[N/A]," \
                " Frame Number[N/A]," \
                " Radar CPU Cycles[N/A]," \
                " Number of detected objects[N/A]," \
				" Number of TLVs[N/A]," \
                " xyzQFormat," \
                "    display count," \
                " aquisition count," \
                " isValid," \
				" isConverted," \
                " x[m]," \
                " y[m]," \
                " z[m]," \
                " doppler[m/s]," \
				" velocity[?]," \
				" rangeIdx[N/A]" \
				" rangeVal[?]" \
				" dopplerIdx[N/A]" \
                " peakValue [?]" \
                " Elevation[N/A]" \
                " Azimuth[N/A]"


# logFileHeader = " Timestamp[ms], Frame Number[N/A], Radar CPU Cycles[N/A], Number of detected objects[N/A], Elevation[mm]"

# logFileHeader = " Aquisition Time[ms]," \
#                 " Frame Number[N/A]," \
#                 " Radar CPU Cycles[N/A]," \
#                 " Number of detected objects[N/A]," \
#                 " xyzQFormat," \
#                 "    display count," \
#                 " aquisition count," \
#                 " isConverted," \
#                 " x[m]," \
#                 " y[m]," \
#                 " z[m]," \
#                 " doppler[m/s]," \
#                 " velocity[?]"
#
# headerFormat = ",{:07d},{:010d},{:011d},{:02d},{:10f}"
# singleEchoFormat = "{:02d},{:02d},{},{:.10f},{:.10f},{:.10f},{:.10f},{:.10f}"
# echoSeparator = "\t"

## END OF FILE
##&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&