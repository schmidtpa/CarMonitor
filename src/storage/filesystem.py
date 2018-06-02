#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Filesystem Persistence
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0
#

import os
import datetime
import hashlib
import uuid
import simplejson as json

class MessageStorage(): 
	
	def __init__(self, config):
		self.cfg = config
		self.messageQueueId = self.generateQueueId()
		self.messageQueue = {}
		
	def run(self, carmonitor):
		self.saveQueuedMessages(carmonitor)
		self.sendQueuedMessages(carmonitor)
		
	def saveQueuedMessages(self, carmonitor):
		for mid in self.messageQueue.keys():
			try:
				message = self.messageQueue[mid]
				
				if not time in message:
					message['time'] = carmonitor.collectorTime
					
				if not file in message:
					message['file'] = None
				
				delta = carmonitor.collectorTime - message['time']
				#print "[CarMonitor::Storage] Message " + str(mid) + " send delta " + str(delta.total_seconds())
				
				if message['file'] is None and delta.total_seconds() >= self.cfg['time']:
					filePath = str(self.cfg['path'] + self.messageQueueId + '_' + str(mid) + '.msg')
					
					jsonData = {
						'topic': message['topic'],
						'payload': message['payload'],
						'qos': message['qos']
					}
					
					msgFile = open(filePath , "w")
					msgFile.write(json.dumps(jsonData))
					msgFile.close()
					
					self.messageQueue[mid]['file'] = filePath
					print "[CarMonitor::Storage] Saved message " + str(mid) + " to " + str(filePath)
				
			except Exception as e:
				print "[CarMonitor::Storage] Error saving message " + str(mid) + ": " + str(e)
				
	def sendQueuedMessages(self, carmonitor):
		for filename in os.listdir(self.cfg['path']):
			if not filename.startswith(self.messageQueueId):
				filePath = self.cfg['path'] + filename
				print "[CarMonitor::Storage] Sending stored message " + str(filePath)
				
				with open(filePath,'r') as jsonFile:
					try:
						jsonData = json.load(jsonFile)
						carmonitor.sendMessage(jsonData['topic'], jsonData['payload'], jsonData['qos'])
						os.remove(filePath)
					except Exception as e:
						print "[CarMonitor::Storage] Error reading file: " + str(e)
						os.remove(filePath)
	
	def saveMessage(self, time, mid, topic, payload, qos):
		self.messageQueue[mid] = {
			'time': time,
			'topic': topic,
			'payload': payload,
			'qos' : qos,
			'file': None
		}
		
		#print "[CarMonitor::Storage] Message " + str(mid) + " queued "

	def removeMessage(self, mid):
		try:
			message = self.messageQueue[mid]
			
			if message['file'] is not None:
				os.remove(message['file'])
				print "[CarMonitor::Storage] Removed message " + str(mid) + " from " + message['file']
				
			del self.messageQueue[mid]
			#print "[CarMonitor::Storage] Removed message " + str(mid)
			
		except KeyError:
			print "[CarMonitor::Storage] Unkown mid to remove " + str(mid)
		except Exception as e:
			print "[CarMonitor::Storage] Error while removing mid " + str(mid) + ": " + str(e)
	
	def generateQueueId(self):
		m = hashlib.md5()
		m.update(str(uuid.uuid4()))
		return str(m.hexdigest())
