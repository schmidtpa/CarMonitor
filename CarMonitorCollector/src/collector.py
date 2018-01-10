#! /usr/bin/python
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0

import time
import os
import Queue

import gpsd
import tracking
import communication

import config

class Collector():

	def __init__(self):
		self.poller = gpsd.GpsdPoller()
		self.tracking = tracking.FileTracking()
		
		self.sendQueue = Queue.Queue()
		self.communication = communication.Communication(self.sendQueue)
		
	def run(self):
		print 'Starting Collector...'
		
		if not self.tracking.checkTrackingPath():
			print 'Aborting...'
		
		try: 
			self.poller.start()
			self.communication.start()

			while True:
				self.gpsdData = self.poller.getGpsdData()
				
				try: 
					# check if result contains compatible data
					if self.gpsdData.keys()[0] == 'epx':

						# check if the car is driving
						if self.gpsdData['speed'] > 0.5:

							# Try to send message to mqtt broker
							self.sendQueue.put(self.gpsdData)
						
							# Save message to file archive
							self.tracking.trackGpsData(gpsdData)
							
							# If speed < 20 m/s sleep for the time needed to drive 20m
							# else sleep for one second if speed >= 20 m/s
							if self.gpsdData['speed'] < 20.0:
								self.sleepTime = 20.0/self.gpsdData['speed']
							else: 
								self.sleepTime = 1.0
						else:
							self.sleepTime = 2.5
					else:
						self.sleepTime = 2.5

					time.sleep(self.sleepTime)
					self.writeConsoleOutput()

				except(AttributeError, KeyError):
					pass
		
		except(KeyboardInterrupt, SystemExit):
			print 'Stopping Collector...'
			self.tracking.close()
			self.communication.join()
			self.poller.join()

	def writeConsoleOutput(self):
		if self.gpsdData != None:
			print 'Time: ' + self.gpsdData['time']
			print 'Position: ' + str(self.gpsdData['lat']) + u" \u00b0, " + str(self.gpsdData['lon']) + u" \u00b0"
			print 'Speed: ' + str(self.gpsdData['speed']) + ' m/s'
		else:
			print 'Time: N/A'
			print 'Position: N/A'
			print 'Speed: N/A'
			
		if self.sleepTime != None:
			print 'Sleep Time: ' + str(self.sleepTime) + ' s'
		else:
			print 'Sleep Time: N/A'
			
		if self.communication != None:
			if self.communication.isConnected():
				print 'Server: connected'
			else:
				print 'Server: disconnected'
				
			print 'Message Cache: ' + str(self.communication.getCacheSize()) + ' Items'
		
if __name__ == '__main__':
	Collector().run()