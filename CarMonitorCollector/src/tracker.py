#! /usr/bin/python
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0

import threading
import Queue
import os
import datetime

import config

class GpsTracker(threading.Thread):
	
	DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

	def __init__(self,inQueue):
		threading.Thread.__init__(self)
		self.stopRequest = threading.Event()
		self.inQueue = inQueue
		self.trackFile = None
		self.trackDate = None
		self.trackData = None
		
	def run(self):
		while not self.stopRequest.isSet():
			try:
				self.trackData = self.inQueue.get(True, 0.05)
				self.checkTrackFile()
				self.storeData()
			except Queue.Empty:
				continue
				
		if not self.trackFile == None:
			self.trackFile.close()
				
	def storeData(self):
		self.trackFile.write(str(self.trackData['time']))
		self.trackFile.write(';')
		self.trackFile.write(str(self.trackData['mode']))
		self.trackFile.write(';')
		self.trackFile.write(str(self.trackData['lon']))
		self.trackFile.write(';')
		self.trackFile.write(str(self.trackData['lat']))
		self.trackFile.write(';')
		self.trackFile.write(str(self.trackData['alt']))
		self.trackFile.write(';')
		self.trackFile.write(str(self.trackData['track']))
		self.trackFile.write(';')
		self.trackFile.write(str(self.trackData['climb']))
		self.trackFile.write(';')
		self.trackFile.write(str(self.trackData['speed']))
		self.trackFile.write(';')
		self.trackFile.write(str(self.trackData['epx']))
		self.trackFile.write(';')
		self.trackFile.write(str(self.trackData['epy']))
		self.trackFile.write(';')
		self.trackFile.write(str(self.trackData['epv']))
		self.trackFile.write(';')
		self.trackFile.write(str(self.trackData['ept']))
		self.trackFile.write('\n')
		self.trackFile.flush()
		
	def checkTrackFile(self):
		now = datetime.datetime.strptime(str(self.trackData['time']),self.DATETIME_FORMAT).date()

		if self.trackDate == None:
			self.trackDate = now

		if self.trackFile == None:
			self.openTrackFile()
			
		if self.trackDate != now:
			self.openTrackFile()
			
	def openTrackFile(self):
		if self.trackFile != None:
			self.trackFile.flush()
			self.trackFile.close()

		fileName = config.TRACK_PATH + '/gpsd_' + self.trackDate.strftime('%Y%m%d') + '.log'

		if os.path.isfile(fileName):
			self.trackFile = open(fileName,'a')
		else:
			self.trackFile = open(fileName,'w')
			self.trackFile.write('Time')
			self.trackFile.write(';')
			self.trackFile.write('Mode')
			self.trackFile.write(';')
			self.trackFile.write('Longitude')
			self.trackFile.write(';')
			self.trackFile.write('Latitude')
			self.trackFile.write(';')
			self.trackFile.write('Altitude')
			self.trackFile.write(';')
			self.trackFile.write('Track')
			self.trackFile.write(';')
			self.trackFile.write('Climb')
			self.trackFile.write(';')
			self.trackFile.write('Speed')
			self.trackFile.write(';')
			self.trackFile.write('epx')
			self.trackFile.write(';')
			self.trackFile.write('epy')
			self.trackFile.write(';')
			self.trackFile.write('epv')
			self.trackFile.write(';')
			self.trackFile.write('ept')
			self.trackFile.write('\n')
			self.trackFile.flush()
			
	def checkTrackPath(self):
		if not os.path.exists(config.TRACK_PATH):
			print 'Track Path ' + config.TRACK_PATH + ' does not exist!'
			return False
			
		if not os.access(config.TRACK_PATH,os.W_OK):
			print 'Track Path ' + config.TRACK_PATH + ' is not writeable!'
			return False
			
		return True
		
	def join(self, timeout=None):
		self.stopRequest.set()
		super(GpsTracker, self).join(timeout)
	