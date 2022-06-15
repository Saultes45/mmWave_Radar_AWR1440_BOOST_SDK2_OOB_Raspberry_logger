#!/bin/sh

################################################################
#
#   This file executes the python script that gets the radar 
#   data and estimate the water elevation
#
################################################################

## Metadata
# Written by    : Nathanael Esnault
# Verified by   : N/A
# Creation date : 2022-05-09
# Version       : 1.0 (finished on ...)


#lxterminal --command="/bin/bash -c '/home/pi/Desktop/LogSonarData.sh; read'"


# Step 1/5 - Create the RadarLogs folder if it doesn't exist, it will contain the console data
#----------------------------------------------------------------------------------------------
if [ ! -d /home/pi/Desktop/RadarLogs  ]; then
  mkdir -p /home/pi/Desktop/RadarLogs ;
fi


# Step 2/5 - Remove the previous file on the Desktop, if it exist
#----------------------------------------------------------------
file="/home/pi/Desktop/RadarStarted.txt"

if [ -f $file ] ; then
    rm $file
fi

# Step 3/5 - Show that the script has started by creating an empty file on the Desktop
#--------------------------------------------------------------------------------------
touch /home/pi/Desktop/RadarStarted.txt


# Step 4/5 - If a console log already exists in the folder, rename it with a timestamp
#--------------------------------------------------------------------------------------
logfile="/home/pi/Desktop/RadarLogs/console.log"
if [ -f "$logfile" ]
	then mv "$logfile" "${logfile%.*}__$(date +%Y-%m-%d__%H-%M-%S__%N).log"
fi


# Step 5/5 - Run the python script and capture its output in the console.log file
#--------------------------------------------------------------------------------
#/home/pi/Desktop/killScreenAfter5s.sh &
#screen /dev/ttyUSB0

#cat /dev/ttyUSB0 | while IFS= read -r line; do echo "$(date +%Y%M%d-%H:%M:%S:%N) $line"; done >> /home/pi/Desktop/GNSSLogs/smallLOG.log

# Minicom is an external program and need to be installed (with package manager)
#minicom -D /dev/ttyACM1 -b 921600


python3  /home/pi/Hello.py 
cd "/home/pi/Desktop/54_WaveRadarT&T/01_FinalCode"
#python3  "/home/pi/Desktop/54_WaveRadarT&T/01_FinalCode/TestConfigParser.py" >> /home/pi/Desktop/RadarLogs/console.log
python3  "/home/pi/Desktop/54_WaveRadarT&T/01_FinalCode/logRadar.py" 2>&1 | tee /home/pi/Desktop/RadarLogs/console.log

#python3  /home/pi/Hello.py >> /home/pi/Desktop/RadarLogs/console.log
#python3  /home/pi/Hello.py  2>&1 | tee info.log

