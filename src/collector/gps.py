#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# CarMonitor Gps Collector
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0
#

import os
import math
import datetime

class GpsCollector():

	def __init__(self, config):
		self.cfg = config
		
		self.update = False
		self.lastGpsdData = None
		
		self.updateTime = None
		self.updateTimeDelta = None
		
	def run(self, carmonitor):
		if carmonitor.gpsdData is None:
			print '[Collector::GPS] GPS data not available'
			return 
		
		if carmonitor.gpsdData['mode'] < 3:
			print '[Collector::GPS] GPS mode 3 required (current: ' + str(carmonitor.gpsdData['mode']) + ')'
			return
		
		# check for last gpsdData
		if self.lastGpsdData is None:
			self.lastGpsdData = carmonitor.gpsdData
			
		# check for last updateTime
		if self.updateTime is None:
			self.updateTime = datetime.datetime.fromtimestamp(0)
			
		# check update time
		self.updateTimeDelta = carmonitor.collectorTime - self.updateTime

		if self.updateTimeDelta.total_seconds() >= self.cfg['timedelta']:
			# print '[Collector::GPS] Reached time threshold (' + str(self.cfg['timedelta']) + ' s): ' + str(self.updateTimeDelta.total_seconds())
			self.update = True
			
		# check speed
		if carmonitor.gpsdData['speed'] >= self.cfg['speed']:
			# print '[Collector::GPS] Reached min speed threshold (' + str(self.cfg['speed']) + ' m/s): ' + str(carmonitor.gpsdData['speed']) + ' m/s'
			self.update = True
			
		# check distance
		gpsdDistance = self.distance(carmonitor.gpsdData['lat'], carmonitor.gpsdData['lon'], self.lastGpsdData['lat'], self.lastGpsdData['lon'])
		
		if gpsdDistance >= self.cfg['distance']:
			# print '[Collector::GPS] Reached max distance threshold (' + str(self.cfg['distance']) + ' m):  ' + str(gpsdDistance) +  'm'
			self.update = True
		
		# process a gps status update and send the new data
		if self.update:
			
			# send the new data
			topic='position'
			
			data = {
				'lat': round(carmonitor.gpsdData['lat'],7),
				'lon': round(carmonitor.gpsdData['lon'],7),
				'alt': round(carmonitor.gpsdData['alt']),
				'speed': round(carmonitor.gpsdData['speed'],4),
				'head': round(carmonitor.gpsdData['heading'],4),
				'climb': round(carmonitor.gpsdData['climbrate'],4),
				'sats': carmonitor.gpsdData['sats'],
				'ex': round(carmonitor.gpsdData['epx'],4),
				'ey': round(carmonitor.gpsdData['epy'],4),
				'ev': round(carmonitor.gpsdData['epv'],4),
				'et': round(carmonitor.gpsdData['ept'],4)
			}
			
			carmonitor.sendMessage(topic, data, 1)
			
			# save last update time
			self.updateTime = carmonitor.collectorTime
			
			# save last gpsdData
			self.lastGpsdData = carmonitor.gpsdData
				
			# reset update status
			self.update = False
	
	def distance(self, latA, lonA, latB, lonB):
		dy = 0.113 * math.fabs(latA - latB) 	# 0.113 = distance between two latitude circles in meters
		dx = 0.0715 * math.fabs(lonA - lonB)	# 0.0715 = distance between two longitude circles in meters
		return math.sqrt(dx * dx + dy * dy)
