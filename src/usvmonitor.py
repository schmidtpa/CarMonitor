#! /usr/bin/python
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0
#
# Written for a JoyIT StromPiV2 
# see https://www.joy-it.net/strompi-2/
# 

import RPi.GPIO as GPIO
import time
import os

# SetUp GPIO for USV Check
GPIO.setmode(GPIO.BCM)
GPIO_TPIN = 21												# select pin 21
GPIO.setup(GPIO_TPIN,GPIO.IN,pull_up_down = GPIO.PUD_DOWN)	# set as input

try:
	print "[USVMonitor] Started StromPiV2"
	
	while GPIO.input(GPIO_TPIN) == 0:
		time.sleep(5.0)
	
	print "[USVMonitor] Shutting down..."
	os.system("sudo shutdown -P now")
	
except KeyboardInterrupt:
	print "[USVMonitor] Stopped on user request."
	
GPIO.cleanup()
