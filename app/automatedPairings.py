from sqlalchemy import func, and_, extract, case
from sqlalchemy.sql import text
from datetime import date, datetime
from app.models import Player, Tournament, Match, Set, Statistics, TournamentType, Entity, EntityParticipant, MatchParticipant
import smtplib
import json
import collections
from app.post import slack_bot
from app.slackapi.channel import channel
from app.slackapi.user import user
from app.slackapi.reactions import getReactions
import app.api
import schedule

from app import app, db


def scheduledPairings():

	schedule.every().day.at("11:45").do(automatePairings())

	while True:
	    schedule.run_pending()
	    time.sleep(60) # wait one minute


def automatePairings():

	with open('app/pairings.settings') as config:
		settings = json.loads(config.read())	

	pairingsChannel = Channel(settings['token'], settings['pairings_channel_name'])
	pairingsMessage = pairingsChannel.getPairingsMessage()

	pairingsMessageReactions = getReactions(pairingsChannel.channelId, pairingsMessage[3])

	for reaction in pairingsMessageReactions:
 		if reaction[0] == 'hand':
 			playList == []
 			playList == reaction[1]

 		if reaction[0] =='metal':
 			draftList == []
 			draftList == reaction[1]

 	if len[draftList] > 6:
 		for player in draftList:
 			if player in playList:
 				playList.remove(player)

 		postDraftingMessage(getPlayerNamesFromSlackNames(draftList))

 	if len[playList] > 1:
		postPairings(getPlayerNamesFromSlackNames(playList))


def postDraftingMessage(playerList):

	with open('app/pairings.settings') as config:
		settings = json.loads(config.read())	

	if app.config['TESTING'] == True:	
		channel = settings['testing_channel_name']
	else:	
		channel = settings['channel_name']
	pairings_bot = slack_bot(settings['channel_url'], channel, settings['bot_name'], settings['bot_icon'])

	if playerList:

		for player in playerList:

			message += player + '\n'

		attachment = {
				'title': "Friends, Romans, Drafters:",
				'text': message,
		    	'color': "#7CD197",
		    	'mrkdwn_in': ["text"]
			  	 }

		pairings_bot.post_attachment(attachment)

