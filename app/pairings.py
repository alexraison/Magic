from sqlalchemy import func, and_, extract, case
from sqlalchemy.sql import text
from datetime import date, datetime
from app.models import Player, Tournament, Match, Set, Statistics, TournamentType, Entity, EntityParticipant, MatchParticipant
from itertools import combinations
import smtplib
import json
import collections
from app.post import slack_bot
from app.mwmatching import maxWeightMatching
import statistics
import os

from app import app, db


def postPairings(playerList):

	twoHeadedPairings = []
	twoHeadedPairings = getTwoHeadedPairings(playerList)

	if twoHeadedPairings:
		for player in flatten([x[1] for x in twoHeadedPairings]):
			playerList.remove(player)

	normalPairings = getPairings(playerList)

	if normalPairings:
		for player in flatten([x[1] for x in normalPairings]):
			playerList.remove(player)

	slackPairings(normalPairings,twoHeadedPairings, playerList)


def getPairings(playerList):

	matches = getMatches(playerList) 

	tournamentWeightings = getTournamentWeightings(matches)

	inputList = []
	for match in matches:
		inputList.append((match[3], match[4], tournamentWeightings[match[2]]))

	outputList = []
	outputList = enumerate(maxWeightMatching(inputList, True))

	pairings = []
	for x in outputList:
		for match in matches:
			if match[3] == x[0] and match[4] == x[1]:
				pairings.append(match)

	sortedPairings = []
	sortedPairings = sorted(pairings, key=lambda tup: tup[2])

	return sortedPairings

def getTwoHeadedPairings(playerList):

	maxNumberOfMatches = int(len(playerList) / 4) 
	matches = getTwoHeadedMatches(playerList)

	potentialPairings = []

	for i in range(maxNumberOfMatches, 0, -1):  
		potentialPairings = list(getAllPossiblePairings(matches, i))
		if potentialPairings:
			break

	if potentialPairings:
		averageTournaments = getAverageTournament(potentialPairings)

		for pairings, averageTournament in zip(potentialPairings, averageTournaments):
			if averageTournament == min(averageTournaments):
				return pairings
				break
			

def getAllPossiblePairings(matches, r):
	
	outputPairings = []
 
	for pairings in combinations(matches, r):
		allPlayers = list(flatten([x[1] for x in pairings]))
		seen = []
		for player in allPlayers:
			if player not in seen:
				seen.append(player)
		if len(seen) == len(allPlayers):
			outputPairings.append(pairings)	

	return outputPairings


def getAverageTournament(potentialPairings):

	averages = []

	for pairings in potentialPairings:
		tournaments = list([x[2] for x in pairings])
		averages.append(statistics.mean(tournaments))

	return averages


def getMatches(playerList):

	matchList = []

	sql = """SELECT tm.name, x.p1name, x.p2name, x.tournamentID, x.p1id, x.p2id
				FROM (SELECT p1.id AS p1id, p1.name AS p1name, p2.id AS p2id, p2.name AS p2name, min(t.id) as tournamentID
					FROM match AS m
					INNER JOIN match_participant AS mp1 ON m.id = mp1.match_id
					INNER JOIN match_participant AS mp2 ON m.id = mp2.match_id AND mp1.entity_id <> mp2.entity_id
					INNER JOIN entity_participant AS ep1 ON ep1.entity_id = mp1.entity_id
					INNER JOIN entity_participant AS ep2 ON ep2.entity_id = mp2.entity_id
					INNER JOIN player AS p1 ON p1.id = ep1.player_id
					INNER JOIN player AS p2 ON p2.id = ep2.player_id
					INNER JOIN tournament AS t ON t.id = m.tournament_id
					INNER JOIN tournament_type AS tt on t.type = tt.id
					WHERE p1.name IN ('""" + "', '".join(playerList) + """')
						AND p2.name IN ('""" + "', '".join(playerList) + """')
						AND mp1.game_wins <> tt.game_wins_required
						AND mp2.game_wins <> tt.game_wins_required
						AND tt.description = 'Normal' 
					GROUP BY p1.id, p1.name, p2.id, p2.name) AS x
				INNER JOIN tournament AS tm
					ON tm.id = x.tournamentID"""

	results = db.session.execute(sql).fetchall()

	for row in results:
		# The SQL will return both (match1,player1,player2,id, p1id, p2id) and (match1,player2,player1,id, p2id, p1id)
		if matchList.count((row[0],[row[2],row[1]],row[3],row[5], row[4])) == 0:
			matchList.append((row[0],[row[1],row[2]],row[3], row[4], row[5]))

	return matchList


def getTwoHeadedMatches(playerList):

	matchList = []

	sql = """SELECT t.name, p1.name, p2.name, p3.name, p4.name, t.id
				FROM match AS m
				INNER JOIN match_participant AS mp1 ON m.id = mp1.match_id
				INNER JOIN match_participant AS mp2 ON m.id = mp2.match_id AND mp1.entity_id <> mp2.entity_id
				INNER JOIN entity_participant AS ep1 ON ep1.entity_id = mp1.entity_id
				INNER JOIN entity_participant AS ep2 ON ep2.entity_id = mp1.entity_id AND ep2.player_id <> ep1.player_id
				INNER JOIN entity_participant AS ep3 ON ep3.entity_id = mp2.entity_id
				INNER JOIN entity_participant AS ep4 ON ep4.entity_id = mp2.entity_id AND ep4.player_id <> ep3.player_id
				INNER JOIN player AS p1 ON p1.id = ep1.player_id
				INNER JOIN player AS p2 ON p2.id = ep2.player_id
				INNER JOIN player AS p3 ON p3.id = ep3.player_id
				INNER JOIN player AS p4 ON p4.id = ep4.player_id
				INNER JOIN tournament AS t ON t.id = m.tournament_id
				INNER JOIN tournament_type AS tt on t.type = tt.id
				WHERE p1.name IN ('""" + "', '".join(playerList) + """')
					AND p2.name IN ('""" + "', '".join(playerList) + """')
					AND p3.name IN ('""" + "', '".join(playerList) + """')
					AND p4.name IN ('""" + "', '".join(playerList) + """')
					AND mp1.game_wins <> tt.game_wins_required
					AND mp2.game_wins <> tt.game_wins_required
					AND tt.description = 'Two Headed Giant'
				GROUP BY t.name, p1.name, p2.name, p3.name, p4.name, t.id"""

	results = db.session.execute(sql).fetchall()

	for row in results:
		matchList.append((row[0],[row[1],row[2],row[3],row[4]],row[5]))

	return matchList 


def slackPairings(normalPairings,twoHeadedPairings, remainder):


	with open('app/pairings.settings') as config:
		settings = json.loads(config.read())	

	if app.config['TESTING'] == True:
		channel = os.environ['TESTING_CHANNEL_ID']
	else:
		channel = os.environ['CHANNEL_ID']
	pairings_bot = slack_bot(channel, settings['bot_name'], settings['bot_icon'])


	if not normalPairings and not twoHeadedPairings:
	 	attachment = {
	 				'title': "Uh oh!",
       				'text': "There are no match pairings. Must be time to draft!",
        			    'color': "#7CD197"
       			 }

	 	pairings_bot.post_attachment(attachment)
	else:	
		attachment = {
					'title': "Today's magical pairings:",
  				    'color': "#7CD197"
  				}

		pairings_bot.post_attachment(attachment)

		if twoHeadedPairings:
			for twoHeadedPairing in twoHeadedPairings:

				message = '*' + twoHeadedPairing[1][0] + '* and *' + twoHeadedPairing[1][1] + '* vs *' + twoHeadedPairing[1][2] + '* and *' + twoHeadedPairing[1][3] + '* \n' + twoHeadedPairing[0] 

				attachment = {
						'text': message,
        		    	'color': "#7CD197",
        		    	'mrkdwn_in': ["text"],
        		    	'fallback': message 
     			  	 }

				pairings_bot.post_attachment(attachment)

		if normalPairings:
			for normalPairing in normalPairings:

				message = '*' + normalPairing[1][0] + '* vs *' + normalPairing[1][1] + '* \n' + normalPairing[0] 

				attachment = {
      					'text': message,
       				    'color': "#7CD197",
       				    'mrkdwn_in': ["text"],
        		    	'fallback': message 
      				 }

				pairings_bot.post_attachment(attachment)

		if remainder:

			message = '*No games for these chumps:*\n'

			for player in remainder:

				message += player + '\n'

			attachment = {
      					'text': message,
       				    'color': "#7CD197",
       				    'mrkdwn_in': ["text"],
        		    	'fallback': message 
      				 }

			pairings_bot.post_attachment(attachment)	



def flatten(l):

	basestring = (str, bytes)
	for el in l:
		if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
			for sub in flatten(el):
				yield sub
		else:
			yield el


def getTournamentWeightings (matches):

	tournaments = []
	for match in matches:
		if tournaments.count(match[2]) == 0:
			tournaments.append(match[2])

	return {t[1]:t[0]*t[0] for t in enumerate(sorted(tournaments, reverse=True))}





