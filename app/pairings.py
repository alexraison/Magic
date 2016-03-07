from sqlalchemy import func, and_, extract, case
from sqlalchemy.sql import text
from datetime import date, datetime
from app.models import Player, Tournament, Match, Set, Statistics, TournamentType, Entity, EntityParticipant, MatchParticipant
from itertools import combinations
import smtplib
import json
import collections
from app.post import slack_bot
import statistics

from app import db


def postPairings(playerList):

	with open('app/pairings.settings') as config:
		settings = json.loads(config.read())

	pairings_bot = slack_bot(settings['pairings_channel_url'], settings['pairings_channel_name'], settings['pairings_bot_name'], settings['pairings_bot_icon'])

	twoHeadedPairings = []
	twoHeadedPairings = getPairings(playerList, True)

	if twoHeadedPairings:
		for player in flatten([x[1] for x in twoHeadedPairings]):
			playerList.remove(player)

	normalPairings = getPairings(playerList, False)

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
        		    	'mrkdwn_in': ["text"]
     			  	 }

				pairings_bot.post_attachment(attachment)

		if normalPairings:
			for normalPairing in normalPairings:

				message = '*' + normalPairing[1][0] + '* vs *' + normalPairing[1][1] + '* \n' + normalPairing[0] 

				attachment = {
      					'text': message,
       				    'color': "#7CD197",
       				    'mrkdwn_in': ["text"]
      				 }

				pairings_bot.post_attachment(attachment)


def getPairings(playerList, twoHeaded):

	if twoHeaded:
		numberOfMatches = int(len(playerList) / 4) 
		matchPairings = getTwoHeadedMatches(playerList)
	else:
		numberOfMatches = int(len(playerList) / 2) 
		matchPairings = getMatches(playerList) 

	potentialPairings = []

	for i in range(numberOfMatches, 0, -1):  
		potentialPairings = list(getPotentialPairings(matchPairings, i))
		if potentialPairings:
			break

	if potentialPairings:
		averageTournaments = getAverageTournament(potentialPairings)

		for pairings, averageTournament in zip(potentialPairings, averageTournaments):
			if averageTournament == min(averageTournaments):
				return pairings
				break
			


def getPotentialPairings(matchPairings, r):
	
	outputPairings = []
 
	for pairings in combinations(matchPairings, r):
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

	sql = """SELECT t.name, p1.name, p2.name, t.id
				FROM match AS m
				INNER JOIN match_participant AS mp1 ON m.id = mp1.match_id
				INNER JOIN match_participant AS mp2 ON m.id = mp2.match_id AND mp1.entity_id <> mp2.entity_id
				INNER JOIN entity_participant AS ep1 ON ep1.entity_id = mp1.entity_id
				INNER JOIN entity_participant AS ep2 ON ep2.entity_id = mp1.entity_id AND ep2.player_id <> ep1.player_id
				INNER JOIN player AS p1 ON p1.id = ep1.player_id
				INNER JOIN player AS p2 ON p2.id = ep2.player_id
				INNER JOIN tournament AS t ON t.id = m.tournament_id
				INNER JOIN tournament_type AS tt on t.type = tt.id
				WHERE p1.name IN ('""" + "', '".join(playerList) + """')
					AND p2.name IN ('""" + "', '".join(playerList) + """')
					AND mp1.game_wins <> tt.game_wins_required
					AND mp2.game_wins <> tt.game_wins_required
					AND tt.description = 'Normal'
				GROUP BY t.name, p1.name, p2.name, t.id"""

	results = db.session.execute(sql).fetchall()

	for row in results:
		try:
			b = matchList.index((row[0],[row[2],row[1]],row[3]))
		except:	
			matchList.append((row[0],[row[1],row[2]],row[3]))
	print(matchList)

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


def flatten(l):

	basestring = (str, bytes)
	for el in l:
		if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
			for sub in flatten(el):
				yield sub
		else:
			yield el






