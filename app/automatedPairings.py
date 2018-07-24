from sqlalchemy import func, and_, extract, case
from sqlalchemy.sql import text
from datetime import date, datetime
from app.models import Player, Tournament, Match, Set, Statistics, TournamentType, Entity, EntityParticipant, MatchParticipant
import smtplib
import json
import collections
from app.post import slack_bot
from app.slackApiUser import User
from app.slackApiChannel import Channel
from app.pairings import postPairings
from app.api import getPlayerNamesFromSlackUsers
import schedule
import time
import os

from app import app

def scheduledPairings():

	with open('app/pairings.settings') as config:
		settings = json.loads(config.read())

	schedule.every().day.at(str(os.environ['PAIRINGS_TIME'])).do(automatePairings)

	while True:
		schedule.run_pending()
		time.sleep(60) # wait one minute


def automatePairings():

	with open('app/pairings.settings') as config:
		settings = json.loads(config.read())

	token = str(os.environ['SLACK_TOKEN'])

	pairingsChannel = Channel(token, settings['pairings_channel_name'])
	pairingsMessage = pairingsChannel.getPairingsMessage()

	pairingsMessageReactions = []
	if pairingsMessage:
		pairingsMessageReactions = pairingsMessage.get('reactions')

	playList = []
	draftList = []
	for reaction in pairingsMessageReactions:
		if reaction['name'] == 'hand':
			for userId in reaction['users']:
				user = User(token, userId)
				playList.append(user.getUserName())

		if reaction['name'] =='metal':
			for userId in reaction['users']:
				user = User(token, userId)
				draftList.append(user.getUserName())

	if len(draftList) > 5:
		for player in draftList:
			if player in playList:
				playList.remove(player)

		drafters = getPlayerNamesFromSlackUsers(draftList)
		postDraftingMessage(drafters)

	if len(playList) > 1:
		players = getPlayerNamesFromSlackUsers(playList)
		postPairings(players)


def postDraftingMessage(playerList):

	with open('app/pairings.settings') as config:
		settings = json.loads(config.read())

	if app.config['TESTING'] == True:
		channel = settings['testing_channel_name']
	else:
		channel = settings['channel_name']
	pairings_bot = slack_bot(settings['channel_url'], channel, settings['bot_name'], settings['bot_icon'])

	if playerList:

		message = ''
		for player in playerList:

			message += player + '\n'

		attachment = {
				'title': "Enough people have raised their horned hands to the God-Pairaoh, and he has answered! Praise Him!",
				'text': message,
				'color': "#7CD197",
				'mrkdwn_in': ["text"]
				 }

		pairings_bot.post_attachment(attachment)

