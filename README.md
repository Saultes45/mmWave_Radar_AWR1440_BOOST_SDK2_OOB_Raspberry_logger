

# mmWave_Radar_AWR1440_BOOST_SDK2_OOB_Raspberry_logger
A repository regrouping the code and knowledge necessary for the wave height detection project in partenership with T+T .


sudo mount /dev/sda1 /mnt/usb

*Keywords:* 

 - mmWave
 - Radar
 - AWR1440 (automotive: CAN)
 - OOB (out of the box demo)
 - SDK 2.1
 - datalogger (Raspberry pi)

This markdown file has been gererated via StackEdit: https://stackedit.io/

## Hardware: 
### Radar:
Firmware: 2.1.0.4 (old)
### Datalogger
Raspberry pi 4B+ with [DS3231 RTC](https://www.jaycar.co.nz/rtc-clock-module-for-raspberry-pi/p/XC9044?pos=1&queryId=4a57b52d89bf715f61d30ddb03578fc9) (Rasbian/N00BS)




## Source:
Heavily based on [ibaiGorordo's code](https://github.com/ibaiGorordo/IWR1443-Read-Data-Python-MMWAVE-SDK-1) (on github): 


## Environment
### Python interpreter tested

 - 3.7.X (Home desktop win7 x64) 
 - 3.7.3 (Uni PGR desktop win 10 x64)

### Python libraries
You also need to install the following libraries via:
 IDLE: pip or pip3 
 PyCharm T*oolbar->File->Setting-> Project interpreter*

 - pyserial V3.5 (latest at the time)
 - numpy V1.22.3 (latest at the time)

## Radar framerate

argument #5 of the CLI command "*frameCfg*"

**18**Hz is 1/18 is 0.055555556s or **55.556**ms

    frameCfg 0 1 16 0 55.556 1 0

**8**Hz is 1/8 is 0.125s or **125**ms

    frameCfg 0 1 16 0 125 1 0

GUI (TI official)
-----------------
mmWave_Demo_Visualizer_2.1.0 (working config, check screenshots)

Kickstarter (RadarIQ)
----------------------
Aaron FULTON - Palmerston North - NEW ZEALAND
https://radariq.io/
https://www.kickstarter.com/projects/radariq/radariq-sensor
Palmerston North, NZ
ESTIMATED DELIVERY: Apr 2021
52 backers

Unofficial matlab codes (name of online repos)
----------------------------------------------

 - F:\Dropbox\54_WaveRadarT&T\04_MatlabCode\**MatlabRawADC (RawADC)**
 - F:\Dropbox\54_WaveRadarT&T\04_MatlabCode\MatlabReadDat\mmWave_reading-master\ **mmWave_reading-master**  (read and parse .dat files)
 - F:\Dropbox\54_WaveRadarT&T\02_ibaiGorordo\ **AWR1843-Read-Data-Python-MMWAVE-SDK-3--master** \matlab code

Previous dropbox folder
------------------------
F:\Dropbox\50_T+T\02_Radar

New dropbox folder
------------------
F:\Dropbox\54_WaveRadarT&T


Config files from the official GUI
----------------------------------
F:\Dropbox\54_WaveRadarT&T\05_Official_mmWaveDemoVisualiser\LastestVersionApril2022

1- accessing data
------------------
ibaiGorordo
IWR1443-Read-Data-Python-MMWAVE-SDK-1
AWR1843-Read-Data-Python-MMWAVE-SDK-3-
AWR1642-Read-Data-Python-MMWAVE-SDK-2

m6c7l (Germany)

https://github.com/m6c7l/pymmw
source/app/plot_detected_objects.py



2- datalogging
----------------
Use Pycharm
https://github.com/Saultes45/trackir_python_pc_datalogger



3- People that have cracked it
------------------------------

Nazaré Big Waves News:
https://nazarewaves.com/en/news/213
Henet demonstration project in Nazare


Ed/Pete, just to reiterate this is to complete the microwave radar system to measure water level looking down – initially just off the side of a wharf etc (i.e. instead of an RBR) but eventually drone mounted which would let us collect short-term surface elevation timeseries (that we could then feed into phase resolving models etc). Looks like these guys have already cracked it 😉

https://nazarewaves.com/en/news/213


Thesis
Hydraulics and drones: observations of water level, bathymetry and water surface
velocity from Unmanned Aerial Vehicles


> Written with [StackEdit](https://stackedit.io/).
