#! /usr/bin/python
# 
# Author: Patrick Schmidt <patrick@ealp-net.at>
# License: Apache License, Version 2.0

import datetime
import config
import os

class FilePersistence():

	FILE_ENDING = '.msg'

	def __init__(self):
		pass
	
	def putMessage(self, key, msg):
		msgFile = open(self.getMessageFileName(key), 'w')
		msgFile.write(msg)
		msgFile.close()
	
	def getMessage(self, key):
		msgFile = open(self.getMessageFileName(key), 'r')
		msg = msgFile.readline()
		msgFile.close()
		return msg
		
	def removeMessage(self, key):
		os.remove(self.getMessageFileName(key))
		
	def getMessageKeys(self):
		keys = []
		
		for file in os.listdir(config.MESSAGE_PATH):
			if file.endswith(self.FILE_ENDING):
				name, ext = os.path.splitext(file)
				keys.append(name)
				
		return keys
		
	def getMessageFileName(self, key):
		return config.MESSAGE_PATH + '/' + key + self.FILE_ENDING
	
	def checkMessagePath(self):	
		if not os.path.exists(config.MESSAGE_PATH):
			print 'Message Path ' + config.MESSAGE_PATH + 'does not exists'
		
			try:
				os.makedirs(config.MESSAGE_PATH)
				print 'Message Path ' + config.MESSAGE_PATH + ' has been created' 
				return True
			except(OSError):
				print 'Message Path ' + config.MESSAGE_PATH + ' can not be created'
				return False
		
		else:
			if not os.access(config.MESSAGE_PATH, os.W_OK):
				print 'Message Path ' + config.MESSAGE_PATH + ' is not writeable'
				return False
			else:
				return True
			
