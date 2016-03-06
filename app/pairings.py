from sqlalchemy import func, and_, extract, case
from sqlalchemy.sql import text
from datetime import date, datetime, timedelta
from app.models import Player, Tournament, Match, Set, Statistics, TournamentType, Entity, EntityParticipant, MatchParticipant
from itertools import permutations
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

	attachment = {
			'title': "Today's magical pairings:",
            'color': "#7CD197"
        }

	pairings_bot.post_attachment(attachment)

	if twoHeadedPairings:
		for twoHeadedPairing in twoHeadedPairings:

			message = pairing[1][0] + ' and ' + pairing[1][1] + ' versus ' + pairing[1][2] + ' and ' + pairing[1][3] 

			attachment = {
					'title': pairing[0],
       		  		'text': message,
        		    'color': "#7CD197"
     		  	 }

			pairings_bot.post_attachment(attachment)

	if normalPairings:
		for normalPairing in normalPairings:

			message = pairing[1][0] + ' versus ' + pairing[1][1] 

			attachment = {
					'title': pairing[0],
      				'text': message,
       			    'color': "#7CD197"
      			 }

			pairings_bot.post_attachment(attachment)



	if not normalPairings and not twoHeadedPairings:
		attachment = {
					'title': "Uh oh!",
      				'text': "There are no match pairings. Must be time to draft!",
       			    'color': "#7CD197"
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

	for i in range(numberOfMatches, 1, -1):  
		potentialPairings = getPotentialPairings(matchPairings, i)
		if potentialPairings:
			break

	oldestMatches = getOldestDates(potentialPairings)

	for pairings, oldestTournament in zip(potentialPairings, oldestMatches):
		if oldestMatches == min(oldestMatches):
			return pairings


def getPotentialPairings(matchPairings, r):
	
	outputPairings = []

	for pairings in permutations(matchPairings, r):
		allPlayers = [flatten([x[1] for x in pairings])]
		seen = []
		for player in allPlayers:
			if player not in seen:
				seen.append(player)
		if len(seen) == len(allPlayers):
			outputPairings.append(pairings)

	return outputPairings


def getOldestDates(potentialPairings):

	outputPairings = []

	for pairings in potentialPairings:
		minDate = min([x[-1] for x in pairings])
		outputPairings.append(minDate)

	return outputPairings


def getMatches(playerList):

	matchList = []

	sql = """SELECT t.name, p1.name, p2.name, t.date
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
				GROUP BY t.name, p1.name, p2.name, t.date"""

	results = db.session.execute(sql).fetchall()

	for row in results:
		matchList.append((row[0],[row[1],row[2]],row[3]))

	return matchList


def getTwoHeadedMatches(playerList):

	matchList = []

	sql = """SELECT t.name, p1.name, p2.name, p3.name, p4.name, t.date
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
				GROUP BY t.name, p1.name, p2.name, p3.name, p4.name, t.date"""

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






