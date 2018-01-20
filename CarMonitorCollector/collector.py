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
	MAX_WAITING_TIME = 10.0
	MIN_SPEED = 0.3

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
		self.oldGpsdTime = None
		self.gpsdTimeDelta = None
		self.timeDeltaToWait = None
		
	def run(self):
		print '[Collector] Starting...'
		
		if not self.tracking.checkTrackingPath():
			print '[Collector] Aborting...'
		
		try: 
			self.poller.start()
			self.client.connect(config.SERVER_HOST, config.SERVER_PORT, config.SERVER_KEEPALIVE)
			self.client.loop_start();
			
			print '[Collector] Maximum time delta: ' + str(self.MAX_WAITING_TIME)
			print '[Collector] Minimum speed: ' + str(self.MIN_SPEED)
			
			while True:
				rawGpsdData = self.poller.getGpsdData()
				
				try: 
					# prepare gpsdData and check for if compatible data has been set
					self.prepareGpsdData(rawGpsdData)
					
					if self.gpsdData != None:
						print "[Collector] Received new data from GPSD"
					
						# calculate new timestamp
						self.gpsdTime = datetime.datetime.strptime(str(self.gpsdData['time']),self.DATETIME_FORMAT)
						
						# check if an old gpsd time stamp exists
						if self.oldGpsdTime is None:
							self.oldGpsdTime = self.gpsdTime	# crate one if not

						# calculate the delta between the timestamps
						if self.gpsdTime > self.oldGpsdTime:
							self.gpsdTimeDelta = self.gpsdTime - self.oldGpsdTime
						else:
							self.gpsdTimeDelta = datetime.timedelta()
						
						# check if delta to wait is set
						if self.timeDeltaToWait is None:
							self.timeDeltaToWait = datetime.timedelta()

						# check if the current delta is greater then delta to wait
						if self.gpsdTimeDelta >= self.timeDeltaToWait:
							print "[Collector] Checking if update is needed..."
						
							# Save old time stamp
							self.oldGpsdTime = self.gpsdTime
						
							# check if the car is driving
							if self.gpsdData['speed'] >= self.MIN_SPEED:
								print "[Collector] Update needed => current speed " + str(self.gpsdData['speed']) + " m/s >= needed speed " + str(self.MIN_SPEED) + " m/s"
							
								# Send message to server
								self.sendMessageToServer()
								
								# Save message to file archive
								self.sendMessageToArchive()
								
								# calculate speed adaptive time to wait
								if self.gpsdData['speed'] < 20.0:
									s = 20.0/self.gpsdData['speed']
									
									if s > self.MAX_WAITING_TIME:
										s = MAX_WAITING_TIME
								else:
									s = 1.0
							else:
								print "[Collector] No update needed => current speed: " + str(self.gpsdData['speed'])
								s = self.MAX_WAITING_TIME
		
							#set new time to wait for next check
							self.timeDeltaToWait = datetime.timedelta(seconds=s)
							
						# Print debug information to screen
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
			
	def sendMessageToServer(self):
		msg = json.dumps(self.gpsdData)
		result, mid = self.client.publish("car/" + str(config.CLIENT_ID) + "/position", payload=msg, qos=0, retain=True)
		print "[Client] send message " + str(mid) + " to the broker"
		
	
	def sendMessageToArchive(self):
		self.tracking.trackGpsdData(self.gpsdTime, self.gpsdData)
	
			
	def printDebugInformation(self):
		if self.gpsdTime is not None:
			print "[Collector] New time: " + self.gpsdTime.isoformat() 
		else:
			print "[Collector] New time: N/A "
			
		if self.oldGpsdTime is not None:
			print "[Collector] Old time: " + self.oldGpsdTime.isoformat() 
		else:
			print "[Collector] Old time: N/A "
	
		if self.gpsdTimeDelta is not None:
			print "[Collector] Current delta: " + str(self.gpsdTimeDelta.total_seconds())
		else:
			print "[Collector] Current delta: N/A"
			
		if self.timeDeltaToWait is not None:
			print "[Collector] Needed delta:  " + str(self.timeDeltaToWait.total_seconds())
		else:
			print "[Collector] Needed delta:  N/A "
		
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