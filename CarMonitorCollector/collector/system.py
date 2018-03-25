#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# CarMonitor System Collector
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0
#

import os
import datetime

class SystemCollector():

	def __init__(self, config):
		self.cfg = config
		
		self.temperature = None
		self.diskusage= None
		self.uptime = None
		
		self.updateTime = None
		self.updateTimeDelta = None
		
	def run(self, carmonitor):
		if self.updateTime is None:
			self.updateTime = datetime.datetime.fromtimestamp(0)
		
		self.updateTimeDelta = carmonitor.collectorTime - self.updateTime
		
		if self.updateTimeDelta.total_seconds() >= self.cfg['timedelta']:
			print '[Collector::System] Send system information'
			self.updateTime = carmonitor.collectorTime
			
			# update system metrics
			self.updateUptime()
			self.updateDiskusage()
			self.updateTemperature()
			
			# send system metrics
			topic = 'collector'
			data = { 
				'uptime': round(self.uptime,0),
				'disk_free': self.diskusage['free'],
				'disk_total': self.diskusage['total'],
				'disk_used': self.diskusage['used'],
				'disk_usedp': self.diskusage['usedp'],
				'temp': round(self.temperature,2)
			}
			carmonitor.sendMessage(topic, data, 1)
			
		
	def updateDiskusage(self):
		stat = os.statvfs('/')
		
		total = stat.f_blocks * stat.f_bsize
		free = stat.f_bfree * stat.f_bsize
		used = (stat.f_blocks - stat.f_bfree) * stat.f_bsize
		usedp = round((float(used) / float(total) * 100), 2)

		self.diskusage = {'free': free, 'total': total, 'used': used, 'usedp': usedp}
		
	def updateUptime(self):
		with open('/proc/uptime', 'r') as f:
			self.uptime = float(f.readline().split()[0])
			
	def updateTemperature(self):
		res = os.popen('cat /sys/class/thermal/thermal_zone0/temp').readline()
		self.temperature = float(res)/1000.0
