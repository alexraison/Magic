
import requests
import json
import os
import time
from datetime import date, datetime
import logging
import string

from app import app


class Channel:

	def __init__(self, token, channelName):
		self.channelName = channelName
		self.token = token
		self.session = requests.session()
		self.history = []

		if app.config['TESTING'] == True:
			self.oldest = 0
		else:
			self.oldest = time.mktime(date.today().timetuple())

		with open('app/pairings.settings') as config:
			settings = json.loads(config.read())	
		

	def getPairingsMessage(self):
		self.getChannelFromList()
		
		for item in self.history:
			if item['type'] == 'message' and item['user'] == 'USLACKBOT' and item['text'] == 'Reminder: <!here> :pear: :ring: s?':
				return item


	def getChannelFromList(self):
		payload = {'token': self.token}

		response = self.session.get('https://slack.com/api/channels.list', params=payload)

		if response.status_code == 200:
			channelListResponse = response.json()
			if channelListResponse['ok']:
				for channel in channelListResponse['channels']:
					if channel['name'] == self.channelName:
						self.channelId = channel['id']
						self.getChannelHistoryForToday()
			

	def getChannelHistoryForToday(self):
		payload = {
		'token' : self.token,
		'channel' : self.channelId,
		'oldest' : self.oldest
		}

		response = self.session.get('https://slack.com/api/channels.history', params=payload)

		if response.status_code == 200:
			historyResponse = response.json()
			if historyResponse['ok']:
				for item in historyResponse['messages']:
					self.history.append(item)



