
import requests
import json
import os


class User:

	def __init__(self, token, userId):
		self.userId = userId
		self.token = token
		self.session = requests.session()


	def getUserName(self):
		self.getUserInfo()
		return self.userName


	def getUserInfo(self):
		payload = {
		'token' : self.token,
		'user' : self.userId
		}

		response = self.session.get('https://slack.com/api/channels.info', params=payload)
		if response.status_code == 200:
			self.parseUserInfo(response.json())
			

	def parseUserInfo(self, userInfoResponse):
		if userInfoResponse['ok']:
			self.userName = userInfoResponse['user']['name']

