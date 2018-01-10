#! /usr/bin/python
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0

from gps import *
import threading

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
