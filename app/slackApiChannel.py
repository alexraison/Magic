
import requests
import json
import os
import time
from datetime import date, datetime
import logging
import string

from app import app


class Channel:

	def __init__(self, token, channelId):
		self.channelId = channelId
		self.token = token
		self.session = requests.session()

	def getPairingsMessage(self):
		for item in self.getChannelHistoryForToday():
			if item['type'] == 'message' and item['user'] == 'USLACKBOT' and item['text'] == 'Reminder: <!here> :pear: :ring: s?':
				return item

	def getChannelHistoryForToday(self):
		payload = {
		'token' : self.token,
		'channel' : self.channelId,
		'oldest' : time.mktime(date.today().timetuple())
		}

		response = self.session.get('https://slack.com/api/channels.history', params=payload)

		if response.status_code == 200:
			historyResponse = response.json()
			if historyResponse['ok']:
				for item in historyResponse['messages']:
					self.history.append(item)



