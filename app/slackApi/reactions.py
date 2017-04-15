
import requests
import json
import os


def getReactions(token, channelId, timestamp):
	session = requests.session()

	message = {
	'token' : token,
	'channel' : channelId,
	'timestamp' : timestamp
	}
	payload = {'payload':json.dumps(message)}

	return parseReactions(session.get('https://slack.com/api/reactions.get', data=payload).json())

def parseReactions(reactionsResponse):
	reactions = []

	if reactionsResponse['ok']:
		for reaction in reactionsResponse['message']['reactions']:
			reactions.append(reaction['name'], reaction['users'])


