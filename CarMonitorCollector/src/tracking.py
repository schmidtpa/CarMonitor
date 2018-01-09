#! /usr/bin/python
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0

import datetime
import config
import os

class FileTracking():

	FILE_ENDING = '.log'
	DELIMITER = ';'

	def __init__(self):
		self.trackFile = None
		self.trackDate = None
		
	def trackGpsMessage(self, gpsMessage):
		self.checkTrackFile(gpsMessage)
		self.writeTrackLine(gpsMessage)
		
	def writeTrackLine(self, gpsMessage):
		self.trackFile.write(str(gpsMessage.time.isoformat()))
		self.trackFile.write(self.DELIMITER)
		self.trackFile.write(str(gpsMessage.mode))
		self.trackFile.write(self.DELIMITER)
		self.trackFile.write(str(gpsMessage.lon))
		self.trackFile.write(self.DELIMITER)
		self.trackFile.write(str(gpsMessage.lat))
		self.trackFile.write(self.DELIMITER)
		self.trackFile.write(str(gpsMessage.alt))
		self.trackFile.write(self.DELIMITER)
		self.trackFile.write(str(gpsMessage.track))
		self.trackFile.write(self.DELIMITER)
		self.trackFile.write(str(gpsMessage.climb))
		self.trackFile.write(self.DELIMITER)
		self.trackFile.write(str(gpsMessage.speed))
		self.trackFile.write(self.DELIMITER)
		self.trackFile.write(str(gpsMessage.epx))
		self.trackFile.write(self.DELIMITER)
		self.trackFile.write(str(gpsMessage.epy))
		self.trackFile.write(self.DELIMITER)
		self.trackFile.write(str(gpsMessage.epv))
		self.trackFile.write(self.DELIMITER)
		self.trackFile.write(str(gpsMessage.ept))
		self.trackFile.write('\n')
		self.trackFile.flush()
	
	def checkTrackFile(self, gpsMessage):
		now = gpsMessage.time

		if self.trackDate == None:
			self.trackDate = now

		if self.trackFile == None:
			self.openTrackFile()
			
		if self.trackDate != now:
			self.openTrackFile()

	def openTrackFile(self):
		self.closeTrackFile()

		fileName = config.TRACK_PATH + '/gpsd_' + self.trackDate.strftime('%Y%m%d') + self.FILE_ENDING

		if os.path.isfile(fileName):
			self.trackFile = open(fileName,'a')
		else:
			self.trackFile = open(fileName,'w')
			self.trackFile.write('Time')
			self.trackFile.write(self.DELIMITER)
			self.trackFile.write('Mode')
			self.trackFile.write(self.DELIMITER)
			self.trackFile.write('Longitude')
			self.trackFile.write(self.DELIMITER)
			self.trackFile.write('Latitude')
			self.trackFile.write(self.DELIMITER)
			self.trackFile.write('Altitude')
			self.trackFile.write(self.DELIMITER)
			self.trackFile.write('Track')
			self.trackFile.write(self.DELIMITER)
			self.trackFile.write('Climb')
			self.trackFile.write(self.DELIMITER)
			self.trackFile.write('Speed')
			self.trackFile.write(self.DELIMITER)
			self.trackFile.write('epx')
			self.trackFile.write(self.DELIMITER)
			self.trackFile.write('epy')
			self.trackFile.write(self.DELIMITER)
			self.trackFile.write('epv')
			self.trackFile.write(self.DELIMITER)
			self.trackFile.write('ept')
			self.trackFile.write('\n')
			self.trackFile.flush()
			
	def closeTrackFile(self):
		if self.trackFile != None:
			self.trackFile.flush()
			self.trackFile.close()
	
	def close(self):
		self.closeTrackFile()
	
	def checkTrackingPath(self):	
		if not os.path.exists(config.TRACK_PATH):
			print 'Tracking Path ' + config.TRACK_PATH + 'does not exists'
		
			try:
				os.makedirs(config.TRACK_PATH)
				print 'Tracking Path ' + config.TRACK_PATH + ' has been created' 
				return True
			except(OSError):
				print 'Tracking Path ' + config.TRACK_PATH + ' can not be created'
				return False
		
		else:
			if not os.access(config.TRACK_PATH, os.W_OK):
				print 'Tracking Path ' + config.TRACK_PATH + ' is not writeable'
				return False
			else:
				return True
			