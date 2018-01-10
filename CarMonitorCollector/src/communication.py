#! /usr/bin/python
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0

import threading
import Queue
import json
import paho.mqtt.client as mqtt

import persistence

import config

class Communication(threading.Thread):

	def __init__(self, sendQueue):
		threading.Thread.__init__(self)
		self.stopRequest = threading.Event()
		
		self.sendQueue = sendQueue
		self.persistence = persistence.FilePersistence()
		
		self.client = mqtt.Client(client_id=config.CLIENT_ID, clean_session=True, protocol=mqtt.MQTTv311, transport="tcp")
		self.client.username_pw_set(config.SERVER_USER, config.SERVER_PASS)	
		self.client.on_connect = self.on_connect
		self.client.on_disconnect = self.on_disconnect
		self.client.on_publish = self.on_publish
		
		self.messageCache = {}
		self.connected = False
		
	def run(self):	
		
		try:
			self.client.connect(config.SERVER_HOST, port=config.SERVER_PORT, keepalive=config.SERVER_KEEPALIVE)
		except Exception:
			pass 
			
		try:
		
			while not self.stopRequest.isSet():
				# Send messages from persistent storage
				self.sendPersistentMessages(10)

				# Try to send the next message in the queue
				try:
					gpsData = self.sendQueue.get(True, 0.05)
					self.sendMessage(gpsData)
				except Queue.Empty:
					pass

				# Loop the client
				self.client.loop(timeout=1.0)
				
		except StopIteration:
			pass 
			
		self.client.disconnect()
		
	def sendMessage(self, gpsData):
		msg = json.dumps(gpsData.data)
		id = str(gpsdData['time']).translate(None, '-T:.Z')
		
		# Send message and store id and mid relation to cache
		result, mid = self.client.publish("car/"+config.CLIENT_ID+"/position/", payload=msg, qos=1, retain=True)
		messageCache[mid] = id
		print 'Message '+ str(mid) + " send to broker"
		
		# Store Message to persistent storage
		self.persistence.putMessage(id, msg)
		print 'Message '+ str(mid) + " saved to persistent storage"

	def sendPersistentMessages(self, max = 10):
		counter = 0
		
		for id in self.persistence.getMessageIds():
			msg = self.persistence.getMessage(id)
			result, mid = self.client.publish("car/"+config.CLIENT_ID+"/position/", payload=msg, qos=1, retain=True)
			messageCache[mid] = id
			
			counter += 1
			
			if counter > max:
				break
		
	def on_publish(self, client, userdata, mid):
		print 'Message '+ str(mid) + " reached the broker"
		
		if mid in self.messageCache:
			self.persistence.removeMessage(self.messageCache['mid'])
			del self.messageIdCache[mid]
			print 'Message '+ str(mid) + " removed from persistent storage"
			
	def on_connect(self, client, userdata, flags, rc):
		if rc == mqtt.CONNACK_ACCEPTED:
			self.connected = True
			print "Connected to " + config.SERVER_HOST + ":" + str(config.SERVER_PORT)
		else:
			print "Connection returned result: " + mqtt.connack_string(rc)
	
	def on_disconnect(self, client, userdata, rc):
		if rc != mqtt.MQTT_ERR_SUCCESS:
			print "Unexpected disconnection from " + config.SERVER_HOST + ":" + str(config.SERVER_PORT)
		else:
			print "Disconnected from " + config.SERVER_HOST + ":" + str(config.SERVER_PORT)
			
		self.connected = False
		
	def isConnected(self):
		return self.connected
		
	def getCacheSize(self):
		return len(self.messageCache)
			
	def join(self, timeout=None):
		self.stopRequest.set()
		super(Communication, self).join(timeout)
		