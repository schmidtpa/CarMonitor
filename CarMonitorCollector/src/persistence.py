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
	
	def putMessage(self, id, msg):
		msgFile = open(self.getMessageFileName(id), 'w')
		msgFile.write(msg)
		msgFile.close()
	
	def getMessage(self, id):
		msgFile = open(self.getMessageFileName(id), 'r')
		msg = msgFile.read().replace('\n', '')
		msgFile.close()
		return msg
		
	def removeMessage(self, id):
		os.remove(self.getMessageFileName(id))
		
	def getMessageIds(self):
		ids = []
		
		for file in os.listdir(config.MESSAGE_PATH):
			if file.endswith(self.FILE_ENDING):
				name, ext = os.path.splitext(file)
				ids.append(name)
				
		return ids
		
	def getMessageFileName(self, id):
		return config.MESSAGE_PATH + '/' + id + self.FILE_ENDING
	
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
			
