#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# CarMonitor Collector 
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0
#

import os
import time
import datetime
import json
import paho.mqtt.client as mqtt

import poller.enviro
import poller.gpsd

import collector.system
import collector.enviro
import collector.gps

import config as cfg

class CarMonitor():
	
	GPS_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
	
	def __init__(self):
		self.client = mqtt.Client(cfg.client['id'], True)
		self.client.tls_set(cfg.server['cert'])
		self.client.username_pw_set(cfg.client['user'], cfg.client['pass'])	
		
		self.client.on_connect = self.onConnect
		self.client.on_disconnect = self.onDisconnect
		self.client.on_publish = self.onPublish
		
		self.connected = False

		self.collectorTime = None
		self.collectorTimeSrc = None
		
		self.gpsdPoller = poller.gpsd.GpsdPoller()
		self.enviroPoller = poller.enviro.EnviroPoller()
		
		self.gpsdData = None
		self.enviroData = None
		
		self.systemCollector = collector.system.SystemCollector(cfg.collector['system'])
		self.enviroCollector = collector.enviro.EnviroCollector(cfg.collector['enviro'])
		self.gpsCollector = collector.gps.GpsCollector(cfg.collector['gps'])


	def run(self):
		print '[CarMonitor] Starting...'

		try: 
			self.gpsdPoller.start()
			self.enviroPoller.start()
			
			self.client.connect(cfg.server['host'], cfg.server['port'],60)
			self.client.loop_start()

			while True:
				self.gpsdData = self.gpsdPoller.getData()
				self.enviroData = self.enviroPoller.getData()
				
				self.updateCollectorTime()
				
				self.systemCollector.run(self)
				self.enviroCollector.run(self)
				self.gpsCollector.run(self)
				
				time.sleep(0.5)

		except(KeyboardInterrupt, SystemExit):
			print '[CarMonitor] Stopping...'
			self.client.loop_stop()
			self.enviroPoller.join()
			self.gpsdPoller.join()
			print '[CarMonitor] Stopped'
	
	def updateCollectorTime(self):
		if self.gpsdData is not None:
			if self.gpsdData['mode'] == 3 and len(str(self.gpsdData['utc'])) >= 24:
				self.collectorTime = datetime.datetime.strptime(str(self.gpsdData['utc']),self.GPS_DATETIME_FORMAT)
				self.collectorTimeSrc = "GPS"
			else:
				self.collectorTime = datetime.datetime.utcnow()
				self.collectorTimeSrc = "SYS"
		else:
			self.collectorTime = datetime.datetime.utcnow()
			self.collectorTimeSrc = "SYS"
			
	def sendMessage(self, topic, data, qos):
		if self.collectorTime is None:
			print "[CarMonitor::MQTT] Cannot send message - no collector time available "
		else:
			topic = 'car/' + cfg.client['id'] + '/' + topic
			timestamp = long(self.collectorTime.strftime("%s"))
			message = {'t': timestamp, 'd': data}
			payload = json.dumps(message)
			
			result, mid = self.client.publish(topic, payload=payload, qos=qos, retain=True)
			print "[CarMonitor::MQTT] Message " + str(mid) + " send to the broker"
			
	def onPublish(self, client, userdata, mid):
		print "[CarMonitor::MQTT] Message " + str(mid) + " reached the broker"
		
		
	def onConnect(self, client, userdata, flags, rc):
		if rc == mqtt.CONNACK_ACCEPTED:
			print "[CarMonitor::MQTT] Connected to " + cfg.server['host'] + ":" + str(cfg.server['port'])
			self.isConnected = True
		else:
			print "[CarMonitor::MQTT] Connection returned result: " + mqtt.connack_string(rc)
	
	def onDisconnect(self, client, userdata, rc):
		if rc != mqtt.MQTT_ERR_SUCCESS:
			print "[CarMonitor::MQTT] Unexpectedly disconnected from " + cfg.server['host'] + ":" + str(cfg.server['port'])
		else:
			print "[CarMonitor::MQTT] Disconnected from " + cfg.server['host'] + ":" + str(cfg.server['port'])	
			
		self.isConnected = False
			
if __name__ == '__main__':
	CarMonitor().run()
