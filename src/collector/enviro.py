#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# CarMonitor Environment Collector
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0
#

import datetime
import math
import numpy

class EnviroCollector():

	def __init__(self, config):
		self.cfg = config
		
		self.updateTime = None
		self.updateTimeDelta = None
		
		self.lastTempValue = None
		self.lastPressureValue = None
		self.lastAccelValue = None
		
		self.updateEnviro = False
		self.updateAccel = False
		
	def run(self, carmonitor):
		if carmonitor.enviroData is None:
			print '[Collector::Enviro] Enviro data not available'
			return 
		
		if self.updateTime is None:
			self.updateTime = datetime.datetime.fromtimestamp(0)
			
		self.updateTimeDelta = carmonitor.collectorTime - self.updateTime
		
		# Check overall environment delta
		if self.updateTimeDelta.total_seconds() >= self.cfg['timedelta']:
			print '[Collector::Enviro] Reached time threshold (' + str(self.cfg['timedelta']) + ' s): ' + str(self.updateTimeDelta.total_seconds())
			self.updateTime = carmonitor.collectorTime
			self.updateEnviro = True
			self.updateAccel = True
			
		# Check temperature
		if self.lastTempValue is None:
			self.lastTempValue = carmonitor.enviroData['temperature']
			
		tempDelta = math.fabs(self.lastTempValue - carmonitor.enviroData['temperature'])
		
		if tempDelta >= self.cfg['temperature']:
			print '[Collector::Enviro] Reached temperature threshold (' + str(tempDelta) + ' °C): ' + str(carmonitor.enviroData['temperature']) + ' °C'
			self.updateEnviro = True
		
		# Check pressure
		if self.lastPressureValue is None:
			self.lastPressureValue = carmonitor.enviroData['pressure']
			
		pressureDelta = math.fabs(self.lastPressureValue - carmonitor.enviroData['pressure'])
		
		if pressureDelta >= self.cfg['pressure']:
			print '[Collector::Enviro] Reached pressure threshold (' + str(pressureDelta) + ' Pa): ' + str(carmonitor.enviroData['pressure']) + ' Pa'
			self.updateEnviro = True
		
		# Check accelerometer
		if self.lastAccelValue is None:
			self.lastAccelValue = carmonitor.enviroData['accelerometer']
			
		xDelta = math.fabs(self.lastAccelValue['x'] - carmonitor.enviroData['accelerometer']['x'])
		yDelta = math.fabs(self.lastAccelValue['y'] - carmonitor.enviroData['accelerometer']['y'])
		zDelta = math.fabs(self.lastAccelValue['z'] - carmonitor.enviroData['accelerometer']['z'])
		maxDelta = self.cfg['accelerometer']
		
		if xDelta >= maxDelta or yDelta >= maxDelta or zDelta >= maxDelta:
			print '[Collector::Enviro] Reached acceleration threshold ('+ str(xDelta) +'/'+ str(yDelta) +'/'+ str(zDelta) +' G)'
			self.updateAccel = True
			
		# Send environment data
		if self.updateEnviro:
			topic = 'weather'
			data = {
				'temperature': round(numpy.nan_to_num(carmonitor.enviroData['temperature']),2),
				'pressure': round(numpy.nan_to_num(carmonitor.enviroData['pressure']),2)
			}
			carmonitor.sendMessage(topic, data, 1)
			
			self.lastTempValue = carmonitor.enviroData['temperature']
			self.lastPressureValue = carmonitor.enviroData['pressure']

			self.updateEnviro= False
		
		# Send acceleration	
		if self.updateAccel:
			topic = 'acceleration'
			
			x = round(carmonitor.enviroData['accelerometer']['x'],6)
			y = round(carmonitor.enviroData['accelerometer']['y'],6)
			z = round(carmonitor.enviroData['accelerometer']['z'],6)
			
			data = {'x': x, 'y': y, 'z':z }
			carmonitor.sendMessage(topic, data, 1)
			
			self.lastAccelValue = carmonitor.enviroData['accelerometer']
			self.updateAccel = False
