#! /usr/bin/python
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0

import os
import time
import datetime
import json
import paho.mqtt.client as mqtt

import gpsd
import tracking

import config

class Collector():

	DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

	def __init__(self):
		self.poller = gpsd.GpsdPoller()
		self.tracking = tracking.FileTracking()
		
		self.client = mqtt.Client(config.CLIENT_ID, True)
		self.client.tls_set(config.SERVER_CERT)
		self.client.username_pw_set(config.SERVER_USER, config.SERVER_PASS)	
		# self.client.will_set("car/"+config.CLIENT_ID+"/position", payload='{"online":false}', qos=1)
		
		self.client.on_connect = self.onConnect
		self.client.on_disconnect = self.onDisconnect
		self.client.on_publish = self.onPublish

		self.gpsdData = None
		self.gpsdTime = None
		
	def run(self):
		print '[Collector] Starting...'
		
		if not self.tracking.checkTrackingPath():
			print '[Collector] Aborting...'
		
		try: 
			self.poller.start()
			self.client.connect(config.SERVER_HOST, config.SERVER_PORT, config.SERVER_KEEPALIVE)
			self.client.loop_start();

			while True:
				rawGpsdData = self.poller.getGpsdData()
				
				try: 
					# check if gpsdData contains compatible data
					if rawGpsdData.keys()[0] == 'epx':
						self.gpsdData = {}
						
						for key in rawGpsdData.keys():
							if key == 'class':
								continue
							if key == 'device':
								continue
		
							self.gpsdData[key] = rawGpsdData.get(key)
					
						self.gpsdTime = datetime.datetime.strptime(str(self.gpsdData['time']),self.DATETIME_FORMAT)
						
						# Print debug information to screen
						print "[Collector] Time: " + self.gpsdTime.isoformat() + ", Speed:" + str(self.gpsdData['speed']) + " m/s"
						print "[Collector] Lat: " + str(self.gpsdData['lat']) + ", Lon: " + str(self.gpsdData['lon']) + ", Alt: " + str(self.gpsdData['alt'])
						
						# Send message to server
						msg = json.dumps(self.gpsdData)
						result, mid = self.client.publish("car/mazda3/position", payload=msg, qos=0, retain=True)
						
						# Save message to file archive
						self.tracking.trackGpsdData(self.gpsdTime, self.gpsdData)
						
						time.sleep(0.5)	
				
				except(AttributeError, KeyError):
					pass

				time.sleep(0.5)	

		except(KeyboardInterrupt, SystemExit):
			print '[Collector] Stopping...'
			self.tracking.close()
			self.client.loop_stop()
			self.poller.join()
			
	def onPublish(self, client, userdata, mid):
		print '[Client] Message '+ str(mid) + " reached the broker"
		
	def onConnect(self, client, userdata, flags, rc):
		if rc == mqtt.CONNACK_ACCEPTED:
			print "[Client] Connected to " + config.SERVER_HOST + ":" + str(config.SERVER_PORT)
		else:
			print "[Client] Connection returned result: " + mqtt.connack_string(rc)
	
	def onDisconnect(self, client, userdata, rc):
		if rc != mqtt.MQTT_ERR_SUCCESS:
			print "[Client] Unexpected disconnection from " + config.SERVER_HOST + ":" + str(config.SERVER_PORT)
		else:
			print "[Client] Disconnected from " + config.SERVER_HOST + ":" + str(config.SERVER_PORT)
			
			
if __name__ == '__main__':
	Collector().run()