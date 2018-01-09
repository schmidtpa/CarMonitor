#! /usr/bin/python
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0

import time
import os

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
		
		self.messageIdCache = {}
		
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
				gpsdData = self.poller.getGpsdData()
				self.msg = None
				
				try: 
					# check if gpsdData is an gpsMessage
					if gpsdData.keys()[0] == 'epx':
						self.msg = gpsd.GpsMessage(gpsdData)
						
						# check if the car is driving
						if self.msg.speed > 0.5:
						
							# Try to send message to mqtt broker
							self.sendMessage(self.msg)
							
							# Save message to file archive
							self.trackMessage(self.msg)
							
							# Try to send 10 persistent messages
							self.sendPersistentMessages(10)

							# If speed < 20 m/s sleep for the time needed to drive 20m
							# else sleep for one second if speed >= 20 m/s
							if self.msg.speed < 20.0:
								self.sleepTime = 20.0/self.msg.speed
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
			
		
	# Send message to MQTT broker
	def sendMessage(self, msg):
		payload = msg.getJsonMessage()
		result, mid = self.client.publish("car/"+config.CLIENT_ID+"/position/", payload=payload, qos=1, retain=True)
		msg.mid = mid
		
		# Save message to file system
		self.messageIdCache[mid] = msg.id
		self.persistence.putMessage(msg.id, msg)
		
	# Track message to file based archive
	def trackMessage(self, msg):
		self.tracking.trackGpsMessage(msg)
		
	# Try to send persistent messages if they are not in the messageCache
	def sendPersistentMessages(self, max = 10):
		counter = 0
	
		for key in self.persistence.getMessageKeys():
			if key in self.messageCache.values():
				continue # Ignore messages from current session
			
			msg = self.persistence.getMessage(key)
			self.sendMessage(msg)
			counter += 1
			
			if counter > max:
				break
			
	def writeConsoleOutput(self):
		if self.msg != None:
			print 'Time: ' + self.msg.time.isoformat()
			print 'Position: ' + str(self.msg.lat) + u" \u00b0, " + str(self.msg.lon) + u" \u00b0"
			print 'Speed: ' + str(self.msg.speed) + ' m/s'
		else
			print 'Time: N/A'
			print 'Position: N/A'
			print 'Speed: N/A'
			
		if self.sleepTime != None:
			print 'Sleep Time: ' + str(self.sleepTime) + ' s'
		else:
			print 'Sleep Time: N/A'
		
		print 'Message Cache: ' + str(len(self.messageCache)) + ' Items'
		
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
		if mid in self.messageCache:
			self.persistence.removeMessage(self.messageIdCache[mid])
			del self.messageIdCache[mid]
			print 'Message '+ str(mid) + " reached the mqtt broker"
		
if __name__ == '__main__':
	Collector().run()