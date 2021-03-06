﻿#!/usr/bin/python
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
import simplejson as json
import paho.mqtt.client as mqtt

import poller.enviro
import poller.gpsd

import collector.system
import collector.enviro
import collector.gps

import config as cfg
import storage.filesystem

class CarMonitor():
	
	GPS_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
	
	def __init__(self):
		self.client = mqtt.Client(cfg.client['id'], True)
		self.client.tls_set(cfg.server['cert'],cfg.client['cert'], cfg.client['key'])
		self.client.username_pw_set(cfg.client['user'], cfg.client['pass'])	
		self.client.will_set('car/' + cfg.client['id'] + '/status', payload='{ "online": 0 }', qos=2, retain=True)
		
		self.client.on_connect = self.onConnect
		self.client.on_disconnect = self.onDisconnect
		self.client.on_publish = self.onPublish
		
		self.isConnected = False
		self.messageStorage = storage.filesystem.MessageStorage(cfg.storage)
		
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

			self.client.connect_async(cfg.server['host'], cfg.server['port'], 60)
			self.client.loop_start()

			while True:
				self.gpsdData = self.gpsdPoller.getData()
				self.enviroData = self.enviroPoller.getData()
				
				self.updateCollectorTime()
				
				self.systemCollector.run(self)
				self.enviroCollector.run(self)
				self.gpsCollector.run(self)
				self.messageStorage.run(self)

				time.sleep(0.5)

		except(KeyboardInterrupt, SystemExit):
			print '[CarMonitor] Stopping...'
			self.client.loop_stop()
			self.messageStorage.flush()
			self.enviroPoller.join()
			self.gpsdPoller.join()
			print '[CarMonitor] Stopped'
			
		except Exception as e:
			print '[CarMonitor] Error: ' + str(e)
			self.run()
	
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
			mqttTopic = 'car/' + cfg.client['id'] + '/' + topic
			
			if cfg.client['prot'] == 'json':
				mqttPayload = self.buildJsonPayload(data)
			elif cfg.client['prot'] == 'influx':
				mqttPayload = self.buildLinePayload(data, topic)
			else:
				print '[CarMonitor::MQTT] Unkown protocol config option "' + cfg.client['prot'] + '"'
				return

			result, mid = self.client.publish(mqttTopic, payload=mqttPayload, qos=qos, retain=True)
			
			if qos > 0:
				self.messageStorage.saveMessage(self.collectorTime, mid, topic, data, qos)
				
			#print "[CarMonitor::MQTT] Message " + str(mid) + " send to the broker"

	def buildJsonPayload(self, data):
		if not 'time' in data:
			epoch = datetime.datetime.utcfromtimestamp(0)
			timestamp = str(long((self.collectorTime - epoch).total_seconds()) * 1000)
			data['time'] = timestamp
			
		return json.dumps(data, ignore_nan=True) # https://simplejson.readthedocs.io/en/latest/#basic-usage
	
	def buildLinePayload(self, data, topic):
		if 'time' in data:
			messageTime = data['time']
			del data['time']
		else:
			messageTime = self.collectorTime
		
		epoch = datetime.datetime.utcfromtimestamp(0)
		timestamp = str(long((messageTime - epoch).total_seconds()) * 1000000000)
		measurement = str(topic)
		tags = 'car=' + str(cfg.client['id'])
		fields = ''
		
		counter = 0
		dataLen = len(data)
		
		for key in data:
			if counter < (dataLen - 1):
				delemiter = ','
			else:
				delemiter = ''
				
			if isinstance(data[key], basestring):
				fields = fields + str(key) + '=' + '"' + str(data[key]) + '"' +  + delemiter
			else:
				fields = fields + str(key) + '=' + str(data[key]) + delemiter

			counter = counter + 1
		
		return measurement + ',' + tags + ' ' + fields + ' ' + timestamp 
	
	def onPublish(self, client, userdata, mid):
		#print "[CarMonitor::MQTT] Message " + str(mid) + " reached the broker"
		self.messageStorage.removeMessage(mid)
		
	def onConnect(self, client, userdata, flags, rc):
		if rc == mqtt.CONNACK_ACCEPTED:
			print "[CarMonitor::MQTT] Connected to " + cfg.server['host'] + ":" + str(cfg.server['port'])
			self.client.publish('car/' + cfg.client['id'] + '/status', payload='{ "online": 1 }', qos=0, retain=False)
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
