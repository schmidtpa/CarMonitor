#! /usr/bin/python
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0

import time
import os
import json

import paho.mqtt.client as mqtt
import gpsd
import tracking
import persistence

import config

class Collector():

	def __init__(self):
		self.poller = gpsd.GpsdPoller()
		self.tracking = tracking.FileTracking()
		self.persistence = persistence.FilePersistence()
		
		self.client = mqtt.Client(client_id=config.CLIENT_ID, clean_session=True, protocol=mqtt.MQTTv311, transport="tcp")
		self.client.username_pw_set(config.SERVER_USER, config.SERVER_PASS)	
		self.client.on_connect = self.on_connect
		self.client.on_disconnect = self.on_disconnect
		self.client.on_publish = self.on_publish
		
	def run(self):
		print 'Starting Collector...'
		
		if not self.tracking.checkTrackingPath():
			print 'Aborting...'
			
		if not self.persistence.checkMessagePath():
			print 'Aborting...'
		
		try: 
			self.poller.start()
			
			self.client.connect_async(config.SERVER_HOST, port=config.SERVER_PORT, keepalive=config.SERVER_KEEPALIVE)
			self.client.loop_start()
		
			while True:
				self.rawData = self.poller.getGpsdData()
				
				try: 
					if self.rawData.keys()[0] == 'epx':
						self.gpsData = {}
						
						for key in self.rawData.keys():
							if key == 'class':
								continue
							if key == 'device':
								continue
						
							self.gpsData[key] = self.rawData.get(key)
						
						if 'speed' in self.gpsData and 'time' in self.gpsData:
							speed = float(self.gpsData['speed'])
							
							if speed > 0.5:
								self.sendGpsData()
								self.trackGpsData()
								
								if speed < 20.0:
									self.sleepTime = 20.0/speed
								else:
									self.sleepTime = 1.0
							else:
								self.sleepTime = 2.5
						else:
							self.sleepTime = 2.5
							
						time.sleep(self.sleepTime)
						self.writeConsoleOutput()
							
				except(AttributeError, KeyError):
					pass
		
		except(KeyboardInterrupt, SystemExit):
			print 'Stopping Collector...'
			self.client.loop_stop()
			self.client.disconnect()
			self.tracking.close()
			self.poller.join()
		
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
		self.tracking.trackGpsdData(self.gpsData)
	
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