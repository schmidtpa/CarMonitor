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
	print "[USVMonitor] Waiting for StromPiV2 to initialize..."
	
	while GPIO.input(GPIO_TPIN)==1:
		pass
		
	print "[USVMonitor] StromPiV2 ready!"
	
	counter = 0
	
	while True :
		Current_State = GPIO.input(GPIO_TPIN)
		
		if Current_State == 1:
			print "[USVMonitor] Running on backup power (" + str(counter) + "/600)"
			counter = counter + 1
		else:
			print "[USVMonitor] Running on main power (0/600)"
			counter = 0
			
		if counter >= 30:
			print "[USVMonitor] Shutting down..."
			time.sleep(1.0)
			os.system("sudo shutdown -h now")
			break
			
		time.sleep(10.0)
		
	print "[USVMonitor] Stopped monitoring script due power outage."

except KeyboardInterrupt:
	print "[USVMonitor] Stopped on user request."
	
GPIO.cleanup()
