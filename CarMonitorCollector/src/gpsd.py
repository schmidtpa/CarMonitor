#! /usr/bin/python
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0

from gps import *
import threading
import datetime
import time
import json

class GpsdPoller(threading.Thread):

	def __init__(self):
		threading.Thread.__init__(self)
		self.stopRequest = threading.Event()
		self.session = gps(mode=WATCH_ENABLE)
		self.gpsdData = None
		
	def getGpsdData(self):
		return self.gpsdData
		
	def run(self):
		try:
			while not self.stopRequest.isSet():
				self.gpsdData = self.session.next()
		except StopIteration:
			pass 
			
	def join(self, timeout=None):
		self.stopRequest.set()
		super(GpsdPoller, self).join(timeout)
		
class GpsMessage:

	DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

	def __init__(self, gpsdData):
		self.id = str(gpsdData['time']).translate(None, '-T:.Z')
		self.mid = None
		
		self.time = datetime.datetime.strptime(str(gpsdData['time']),self.DATETIME_FORMAT)
		self.mode = int(gpsdData['mode'])
		
		self.lat = float(gpsdData['lat'])
		self.lon = float(gpsdData['lon'])
		self.alt = float(gpsdData['alt'])
		
		self.speed = float(gpsdData['speed'])
		self.track = float(gpsdData['track'])
		self.climb = float(gpsdData['climb'])
		
		self.epx = float(gpsdData['epx'])
		self.epy = float(gpsdData['epy'])
		self.epv = float(gpsdData['epv'])
		self.ept = float(gpsdData['ept'])
		
	def getJsonMessage(self):
		msg = []
		msg['time'] = int(time.mktime(self.time.timetuple()))
		msg['mode'] = self.mode
		
		msg['lat'] = self.lat
		msg['lon'] = self.lon
		msg['alt'] = self.alt
		
		msg['speed'] = self.speed
		msg['track'] = self.track
		msg['climb'] = self.climb
		
		msg['epx'] = self.epx
		msg['epy'] = self.epy
		msg['epv'] = self.epv
		msg['ept'] = self.ept
		
		return json.dumps(msg)
		
	def getMessageTimeDelta(self, now):
		delta = now - self.time
		return delta.total_seconds()
