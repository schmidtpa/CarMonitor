#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# CarMonitor EnviroPHAT Polling Thread and LED Interface
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0
#
# See: https://shop.pimoroni.de/products/enviro-phat
# See: https://learn.pimoroni.com/tutorial/sandyj/getting-started-with-enviro-phat
# See: https://learn.pimoroni.com/tutorial/sandyj/getting-started-with-enviro-phat
# See: http://docs.pimoroni.com/envirophat/
#

from envirophat import weather, leds, motion
import threading
import time

class EnviroPoller(threading.Thread):

	def __init__(self):
		threading.Thread.__init__(self)
		self.stopRequest = threading.Event()
		self.enviroData = None
		self.ledStatus = True
		
	def run(self):
		print '[CarMonitor::EnviroPoller] Starting...'
		
		try:
			while not self.stopRequest.isSet():
				temperature = weather.temperature()
				pressure = weather.pressure()
				accelerometer = motion.accelerometer()
				magnetometer = motion.magnetometer()
				heading = motion.heading()
				
				self.enviroData = {
					'temperature': temperature, 
					'pressure': pressure,
					'accelerometer': {'x': accelerometer.x, 'y': accelerometer.y, 'z': accelerometer.z },
					'magnetometer': {'x': magnetometer.x, 'y': magnetometer.y, 'z': magnetometer.z },
					'heading': heading
				}
				
				time.sleep(.5)
				
		except StopIteration:
			pass 
		
	def getData(self):
		return self.enviroData
	
	def ledOn(self):
		self.ledStatus = True
		leds.on()
		
	def ledOff(self):
		self.ledStatus = False
		leds.off()
		
	def ledToggle(self):
		if self.ledStatus:
			self.ledOff()
		else:
			self.ledOn()
			
	def join(self, timeout=None):
		self.stopRequest.set()
		print '[CarMonitor::EnviroPoller] Stopping...'
		super(EnviroPoller, self).join(10)
