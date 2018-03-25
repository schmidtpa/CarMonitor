#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# CarMonitor GPSD Polling Thread
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0
#

from gps import *
from datetime import datetime
import threading

class GpsdPoller(threading.Thread):

	def __init__(self):
		threading.Thread.__init__(self)
		self.stopRequest = threading.Event()
		self.session = gps(mode=WATCH_ENABLE)
		
	def getData(self):
		gpsdData = {
					'time': self.session.fix.time,
					'utc' : self.session.utc,
					'mode': self.session.fix.mode,
					'lon': self.session.fix.longitude,
					'lat': self.session.fix.latitude,
					'alt': self.session.fix.altitude,
					'speed': self.session.fix.speed,
					'heading': self.session.fix.track,
					'climbrate': self.session.fix.climb,
					'epx': self.session.fix.epx,
					'epy': self.session.fix.epy,
					'epv': self.session.fix.epv,
					'ept': self.session.fix.ept,
					'sats': len(self.session.satellites)
		}
		
		return gpsdData

	def run(self):
		print '[CarMonitor::GpsdPoller] Starting...'
		
		try:
			while not self.stopRequest.isSet():
				self.session.next()
		except StopIteration:
			pass 

	def join(self, timeout=None):
		self.stopRequest.set()
		print '[CarMonitor::GpsdPoller] Stopping...'
		super(GpsdPoller, self).join(10)
