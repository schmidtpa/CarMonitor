#! /usr/bin/python
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0

import time
import gpsd
import Queue
import json
import os
import paho.mqtt.client as mqtt
import tracker

import config

class Collector():

	def __init__(self):
		self.trackerQueue = Queue.Queue()
		
		self.gpsdPoller = gpsd.GpsdPoller()
		self.gpsTracker = tracker.GpsTracker(self.trackerQueue)
		
		self.client = mqtt.Client(client_id=config.CLIENT_ID, clean_session=True, protocol=mqtt.MQTTv311, transport="tcp")
		self.client.username_pw_set(config.SERVER_USER, config.SERVER_PASS)
		
		self.client.on_connect = self.on_connect
		self.client.on_disconnect = self.on_disconnect
		self.client.on_publish = self.on_publish
		
	def run(self):
		print 'Starting Collector...'
		
		if not self.gpsTracker.checkTrackPath():
			print 'Aborting...'
		
		try: 
			self.gpsdPoller.start()
			self.gpsTracker.start()
			
			self.client.connect_async(config.SERVER_HOST, port=config.SERVER_PORT, keepalive=config.SERVER_KEEPALIVE)
			self.client.loop_start()
		
			while True:
				self.rawData = self.gpsdPoller.getGpsData()
				
				try: 
					if self.rawData.keys()[0] == 'epx':
						self.gpsData = {}
						
						for key in self.rawData.keys():
							if key == 'class':
								continue
							if key == 'device':
								continue
						
							self.gpsData[key] = self.rawData.get(key)
						
						if 'speed' in self.gpsData:
							speed = float(self.gpsData['speed'])
							
							if speed > 0.5:
								self.sendGpsData()
								self.trackGpsData()
								self.sleepTime = float(config.TRACK_TARGET_SPEED)/speed
							else:
								self.sleepTime = 1
						else:
							self.sleepTime = 1
							
						time.sleep(self.sleepTime)
						self.writeConsoleOutput()
							
				except(AttributeError, KeyError):
					pass
		
		except(KeyboardInterrupt, SystemExit):
			print 'Stopping Collector...'
			self.client.loop_stop()
			self.client.disconnect()
			self.gpsTracker.join()
			self.gpsdPoller.join()
		
	def on_connect(self, client, userdata, flags, rc):
		if rc == mqtt.CONNACK_ACCEPTED:
			print "Connected to " + config.SERVER_HOST + ":" + str(config.SERVER_PORT)
		else:
			print "Connection returned result: " + mqtt.connack_string(rc)
	
	def on_disconnect(self, client, userdata, rc):
		if rc != mqtt.MQTT_ERR_SUCCESS:
			print "Unexpected disconnection from " + config.SERVER_HOST + ":" + str(config.SERVER_PORT)
		else:
			print "Disconnected from " + config.SERVER_HOST + ":" + str(config.SERVER_PORT)
		
	def on_publish(self, client, userdata, mid):
		print str(mid) + " reached the broker"
		
	def sendGpsData(self):
		msg = json.dumps(self.gpsData)
		self.client.publish("car/"+config.CLIENT_ID+"/position/", payload=msg, qos=1, retain=True)
	
	def trackGpsData(self):
		self.trackerQueue.put(self.gpsData)
	
	def writeConsoleOutput(self):
		os.system('clear')
		print 'CarMonitor Collector'
		print ''
		print 'Collector'
		print '  Target Speed: ' + str(config.TRACK_SPEED) + ' m/s'
		print '  Wait Time: ' + str(self.sleepTime) + ' s'
		print '  Track Queue: ' + str(self.trackerQueue.qsize()) + ' Items'
		print ''
		print 'GPS-Data:'
		print '  Time: ' + str(self.gpsData['time'])
		print '  Latitude: ' + str(self.gpsData['lat']) + u" \u00b0"
		print '  Longitude: ' + str(self.gpsData['lon']) + u" \u00b0"
		print '  Altitude: ' + str(self.gpsData['alt']) + ' m'
		print '  Speed: ' + str(self.gpsData['speed']) + ' m/s'
		print '  Track: '+ str(self.gpsData['track']) + u" \u00b0"
		print '  Climb: ' + str(self.gpsData['climb']) + ' m/s'
		print ''
		
if __name__ == '__main__':
	Collector().run()