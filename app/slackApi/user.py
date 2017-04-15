
import requests
import json
import os

class User:

	def __init__(self, token, userId):
		self.userId = userId
		self.token = token
		self.session = requests.session()

	def getUserName(self):
		getUserInfo(self)
		return self.userName

	def getUserInfo(self):
		message = {
		'token' : self.token,
		'user' : self.userId
		}
		payload = {'payload':json.dumps(message)}

		parseUserInfo(self, self.session.get('https://slack.com/api/users.info', data=payload).json())

	def parseUserInfo(self, userInfoResponse):
		if userInfoResponse['ok'] and not userInfoResponse['deleted']:
			self.userName = userInfoResponse['name']

}