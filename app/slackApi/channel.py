
import requests
import json
import os
import time
from datetime import date, datetime

class Channel:

	def __init__(self, token, channelName):
		self.channelName = channelName
		self.token = token
		self.session = requests.session()
		self.oldest = time.mktime(datetime.date.today().timetuple())

	def getPairingsMessage(self):
		getChannelFromList(self)

		for item in self.history:
			if item[0] == ['message'] and item[1] == ['USLACKBOT'] and item[2] == 'Reminder: <!here> :pear: :ring: s?':
				return item

	def getChannelFromList(self):
		payload = {'payload':json.dumps({'token': self.token})}

		parseChannelFromList(self, self.session.get('https://slack.com/api/channels.list', data=payload)).json())

	def parseChannelFromList(self, channeLListResponse):
		if userInfoResponse['ok']:
			for channel in channeLListResponse['channels']:
				if channel['name'] == self.channelName:
					self.channelId = channel['id']
					getChannelHistory(self)

	def getChannelHistoryForToday(self):
		message = {
		'token' : self.token,
		'channel' : self.channelId,
		'oldest' : self.oldest
		}
		payload = {'payload':json.dumps(message)}

		parseChannelHistory(self, self.session.get('https://slack.com/api/channels.history', data=payload))

	def parseChannelhistory(self, historyResponse):
		self.history = []

		if historyResponse['ok']:
			for item in historyResponse['messages']:
				self.history.append(item['type'], item['user'], item['text'], item['ts'])

}



