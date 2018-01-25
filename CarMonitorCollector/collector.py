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
	
	MAX_WAITING_TIME = 10.0 # Maximum time to wait between to checks in seconds
	MIN_SPEED = 0.5			# Minimum speed in meter per seconds for an update
	MAX_DISTANCE = 20		# Maximum distance between to gps points in meters for an update
	MAX_TIME = 	900			# Maximum time in seconds between two gps datums for an update

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
		self.oldGpsdData = None
		
		self.gpsdTime = None
		self.oldGpsdTime = None
		self.sendGpsdTime = None
		
		self.gpsdTimeDelta = None
		self.timeDeltaToWait = None
		self.sendTimeDelta = None
		
		self.gpsdDistance = None
		
	def run(self):
		print '[Collector] Starting...'
		
		if not self.tracking.checkTrackingPath():
			print '[Collector] Aborting...'
		
		try: 
			self.poller.start()
			self.client.connect(config.SERVER_HOST, config.SERVER_PORT, config.SERVER_KEEPALIVE)
			self.client.loop_start();
			
			print '[Collector] Maximum time delta: ' + str(self.MAX_WAITING_TIME) + " s"
			print '[Collector] Minimum speed: ' + str(self.MIN_SPEED) + " m/s"
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
						
						# check if an old gpsd time stamp exists
						if self.oldGpsdTime is None:
							self.oldGpsdTime = self.gpsdTime		# create one if not
							
						# check if an old gpsd send time stamp exists
						if self.sendGpsdTime is None:
							self.sendGpsdTime = self.gpsdTime		# create one if not do send data after start 
							
						# check if old gpsd data exists
						if self.oldGpsdData is None:
							self.oldGpsdData = self.gpsdData		# copy if not

						# calculate the delta between the timestamps
						if self.gpsdTime > self.oldGpsdTime:
							self.gpsdTimeDelta = self.gpsdTime - self.oldGpsdTime
						else:
							self.gpsdTimeDelta = datetime.timedelta()
						
						# check if delta to wait is set
						if self.timeDeltaToWait is None:
							self.timeDeltaToWait = datetime.timedelta()
							
						# check if an update is needed
						if self.gpsdTimeDelta >= self.timeDeltaToWait:
							print "[Collector] Checking if update is needed..."
							update = False
						
							# Save old time stamp
							self.oldGpsdTime = self.gpsdTime
							
							# Save old data
							self.oldGpsdData = self.gpsdData
							
							# calculate the distance between the current and the old position
							self.gpsdDistance = self.distance(self.gpsdData['lat'], self.gpsdData['lon'], self.oldGpsdData['lat'], self.oldGpsdData['lat'])
						
							# check if the car is fast enough 
							if self.gpsdData['speed'] >= self.MIN_SPEED:
								print "[Collector] Update needed => current speed " + str(self.gpsdData['speed']) + " m/s >= needed speed " + str(self.MIN_SPEED) + " m/s"
								update = True
							else:
								print "[Collector] No update needed => current speed " + str(self.gpsdData['speed']) + " m/s < needed speed " + str(self.MIN_SPEED) + " m/s"
								
							# or if the maximum distance is reached
							if self.gpsdDistance >= self.MAX_DISTANCE:
								print "[Collector] Update needed => current distance " + str(self.gpsdDistance) + " m >= max distance " + str(self.MAX_DISTANCE) + " m"
								update = True
							else:
								print "[Collector] No update needed => current distance " + str(self.gpsdDistance) + " m < max distance " + str(self.MAX_DISTANCE) + " m"
								
							# or if the maximum time is reached
							if self.sendGpsdTime is not None:
								self.sendTimeDelta = self.gpsdTime - self.sendGpsdTime
								
								if self.sendTimeDelta.total_seconds() >= self.MAX_TIME:
									print "[Collector] Update needed => current send delta " + str(self.sendTimeDelta.total_seconds()) + " s >= max send delta " + str(self.MAX_TIME) + "s"
									update = True
								else:
									print "[Collector] No update needed => current send delta " + str(self.sendTimeDelta.total_seconds()) + " s < max send delta " + str(self.MAX_TIME) + "s"
								
							# send data if an update is needed and calculate a new waiting time
							if update:
								# Save last send time
								self.sendGpsdTime = self.gpsdTime

								# Send message to server
								self.sendMessageToServer()
								
								# Save message to file archive
								self.sendMessageToArchive()
								
								# calculate speed adaptive time to wait
								if self.gpsdData['speed'] < 20.0:
									s = 20.0/self.gpsdData['speed']
									
									if s > self.MAX_WAITING_TIME:
										s = self.MAX_WAITING_TIME
								else:
									s = 1.0
							else:
								s = self.MAX_WAITING_TIME
		
							#set new time to wait for next check
							self.timeDeltaToWait = datetime.timedelta(seconds=s)
							
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
		msgData = self.gpsdData
		
		if self.sendTimeDelta is not None:
			msgData['delta'] = self.sendTimeDelta.total_seconds()
			
		if self.gpsdDistance is not None:
			msgData['dist'] = self.gpsdDistance

		msg = json.dumps(msgData)
		result, mid = self.client.publish("car/" + str(config.CLIENT_ID) + "/position", payload=msg, qos=0, retain=True)
		print "[Client] send message " + str(mid) + " to the broker"
	
	def sendMessageToArchive(self):
		self.tracking.trackGpsdData(self.gpsdTime, self.gpsdData)
			
	def printDebugInformation(self):
		if self.gpsdTime is not None:
			print "[Collector] Time: " + self.gpsdTime.isoformat() 
		else:
			print "[Collector] Time: N/A "

		if self.gpsdTimeDelta is not None and self.timeDeltaToWait is not None:
			print "[Collector] Next check: " + str(self.timeDeltaToWait.total_seconds()-self.gpsdTimeDelta.total_seconds()) + " s"
		else:
			print "[Collector] Next check: N/A"
			
		if self.gpsdDistance is not None:
			print "[Collector] Distance: " + str(self.gpsdDistance) + " m"
		else:
			print "[Collector] Distance: N/A "
			
		if self.sendTimeDelta is not None:
			print "[Collector] Send delta: " + str(self.sendTimeDelta.total_seconds()) + " s"
		else:
			print "[Collector] Send delta: N/A "
		
		if self.gpsdData is not None:
			print "[Collector] Lat: " + str(self.gpsdData['lat']) + ", Lon: " + str(self.gpsdData['lon']) + ", Alt: " + str(self.gpsdData['alt']) + ", Speed: " + str(self.gpsdData['speed']) + " m/s"
		else:
			print "[Collector] Lat: N/A, Lon: N/A, Alt: N/A, Speed: N/A"

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
