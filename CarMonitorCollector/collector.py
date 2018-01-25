#! /usr/bin/python
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0

import os
import time
import datetime
import json
import math
import paho.mqtt.client as mqtt

import gpsd
import tracking

import config

class Collector():

	DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
	
	MIN_SPEED = 0.5		# Minimum speed in meter per seconds to trigger an update
	MAX_DISTANCE = 20	# Maximum distance between to gps locations in meters to trigger an update
	MAX_DELTA = 60		# Maximum delta in seconds between two gps reports to trigger an update

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
		
		self.lastGpsdData = None
		self.updateTime = None
		self.updateTimeDelta = None
		self.gpsdDistance = None
		
		self.update = True
		
	def run(self):
		print '[Collector] Starting...'
		
		if not self.tracking.checkTrackingPath():
			print '[Collector] Aborting...'
		
		try: 
			self.poller.start()
			self.client.connect(config.SERVER_HOST, config.SERVER_PORT, config.SERVER_KEEPALIVE)
			self.client.loop_start();
			
			print '[Collector] Minimum speed: ' + str(self.MIN_SPEED) + " m/s"
			print '[Collector] Maximum delta: ' + str(self.MAX_DELTA) + " s"
			print '[Collector] Maximum distance: ' + str(self.MAX_DISTANCE) + " m"
			
			while True:
				rawGpsdData = self.poller.getGpsdData()
				
				try: 
					# prepare gpsdData and check for if compatible data has been set
					self.prepareGpsdData(rawGpsdData)
					
					if self.gpsdData != None:
						print "\n[Collector] Received new data from GPSD"
						
						# calculate new timestamp
						self.gpsdTime = datetime.datetime.strptime(str(self.gpsdData['time']),self.DATETIME_FORMAT)
						
						# check for last gpsdData
						if self.lastGpsdData is None:
							self.lastGpsdData = self.gpsdData
							
						# check for last updateTime
						if self.updateTime is None:
							self.updateTime = self.gpsdTime
						
						# check speed
						if self.gpsdData['speed'] >= self.MIN_SPEED:
							print "[Collector] Need Update: current speed (" + str(self.gpsdData['speed']) + " m/s) >= " + str(self.MIN_SPEED) + " m/s"
							self.update = True
							
						# check distance
						self.gpsdDistance = self.distance(self.gpsdData['lat'], self.gpsdData['lon'], self.lastGpsdData['lat'], self.lastGpsdData['lat'])
						
						if self.gpsdDistance >= self.MAX_DISTANCE:
							print "[Collector] Need Update: current distance (" + str(self.gpsdDistance) + " m) >= + " str(self.MAX_DISTANCE) + " m" 
							self.update = True
						
						# check send time
						self.updateTimeDelta = self.gpsdTime - self.updateTime
						
						if self.updateTimeDelta.total_seconds() >= self.MAX_DELTA:
							print "[Collector] Need Update: current update delta (" + str(self.updateTimeDelta.total_seconds()) + " s) >= + " str(self.MAX_DELTA) + " s"
							self.update = True
							
						# process a gps status update
						if self.update:
							
							# send message to server
							self.sendMessageToServer()
								
							# save message to file archive
							self.sendMessageToArchive()
							
							# save last update time
							self.updateTime = self.gpsdTime
							
							# save last gpsdData
							self.lastGpsdData = self.gpsdData
								
							# reset update status
							self.update = False

						# print debug information to screen
						self.printDebugInformation()
						
						time.sleep(0.5)
					else:
						print "[Collector] No data received from GPSD"
					
				except(AttributeError, KeyError):
					pass
				
				time.sleep(0.5)	
				
		except(KeyboardInterrupt, SystemExit):
			print '[Collector] Stopping...'
			self.tracking.close()
			self.client.loop_stop()
			self.poller.join()

	def distance(self, latA, lonA, latB, lonB):
		dy = 0.113 * math.fabs(latA - latB) 	# 0.113 = distance between two latitude circles in meters
		dx = 0.0715 * math.fabs(lonA - lonB)	# 0.0715 = distance between two longitude circles in meters
		return math.sqrt(dx * dx + dy * dy)
			
	def sendMessageToServer(self):
		msg = json.dumps(self.gpsdData)
		result, mid = self.client.publish("car/" + str(config.CLIENT_ID) + "/position", payload=msg, qos=0, retain=True)
		print "[Client] send message " + str(mid) + " to the broker"
	
	def sendMessageToArchive(self):
		self.tracking.trackGpsdData(self.gpsdTime, self.gpsdData)
			
	def printDebugInformation(self):
		if self.gpsdTime is not None:
			print "[Collector] Time: " + self.gpsdTime.isoformat() 
		else:
			print "[Collector] Time: N/A "

		if self.updateTimeDelta is not None:
			print "[Collector] Update delta " + str(self.updateTimeDelta.total_seconds()) + "/" + str(self.MAX_DELTA) + " s"
		else:
			print "[Collector] Update delta: N/A"
			
		if self.gpsdDistance is not None:
			print "[Collector] Update distance: " + str(self.gpsdDistance) + "/" + str(self.MAX_DISTANCE) + " m"
		else:
			print "[Collector] Update distance: N/A "

		if self.gpsdData is not None:
			print "[Collector] Update speed: " + str(self.gpsdData['speed']) + "/" + str(self.MIN_SPEED) + " m/s"
			print "[Collector] Lat: " + str(self.gpsdData['lat']) + ", Lon: " + str(self.gpsdData['lon']) + ", Alt: " + str(self.gpsdData['alt'])
		else:
			print "[Collector] Update speed: N/A "
			print "[Collector] Lat: N/A, Lon: N/A, Alt: N/A"

	def prepareGpsdData(self, rawGpsdData):
		if rawGpsdData.keys()[0] == 'epx':
			self.gpsdData = {}
						
			for key in rawGpsdData.keys():
				if key == 'class':
					continue
				if key == 'device':
					continue
		
				self.gpsdData[key] = rawGpsdData.get(key)
		else:
			self.gpsdData = None
			
	def onPublish(self, client, userdata, mid):
		print "[Client] Message " + str(mid) + " reached the broker"
		
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
