#! /usr/bin/python
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0

import time
import gpsd
import Queue
import json
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
				rawData = self.gpsdPoller.getGpsData()
				
				try: 
					if rawData.keys()[0] == 'epx':
						gpsData = {}
						
						for key in rawData.keys():
							if key == 'class':
								continue
							if key == 'device':
								continue
						
							gpsData[key] = rawData.get(key)
						
						msg = json.dumps(gpsData)
						self.client.publish("car/"+config.CLIENT_ID+"/position/", payload=msg, qos=1, retain=True)
						self.trackerQueue.put(gpsData)
						print str(gpsData['time']) + ';' + str(gpsData['lon']) + ';' + str(gpsData['lat']) + ';' + str(gpsData['alt']) + ';' + str(gpsData['speed'])
						
					time.sleep(.5)
				
				except(AttributeError, KeyError):
					pass 
				
				time.sleep(0.5)
		
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
		
if __name__ == '__main__':
	Collector().run()