from sqlalchemy import func, and_, extract, case
from sqlalchemy.sql import text
from datetime import date
from itertools import permutations
import smtplib
import json
from app.post import slack_bot
import statistics

from app import db


def postPairings(playerList):

	with open('app/pairings.settings') as config:
		settings = json.loads(config.read())

	pairings_bot = slack_bot(settings['pairings_channel_url'], settings['pairings_channel_name'], settings['pairings_bot_name'], settings['pairings_bot_icon'])


	twoHeadedPairings = getPairings(playerList, True)

	for player in flatten([x[1] for x in twoHeadedPairings]):
		playerList.remove(player)

	normalPairings = getPairings(playerList, False)

	attachment = {
			'title': "Today's magical pairings:",
            'color': "#7CD197"
        }

	results_bot.post_attachment(attachment)

	for twoHeadedPairing in twoHeadedPairings:

		message = pairing[1][0] + ' and ' + pairing[1][1] + ' versus ' + pairing[1][2] + ' and ' + pairing[1][3] 

		attachment = {
				'title': pairing[0],
       	  		'text': message,
        	    'color': "#7CD197"
     	  	 }

		results_bot.post_attachment(attachment)

	for normalPairing in normalPairings:

		message = pairing[1][0] + ' versus ' + pairing[1][1] 

		attachment = {
				'title': pairing[0],
       	  		'text': message,
        	    'color': "#7CD197"
     	  	 }

		results_bot.post_attachment(attachment)


def getPairings(playerList, twoHeaded):

	if twoHeaded:
		numberOfMatches = int(len(playerList) / 4) 
		matchPairings = getMatches(playerList) 
	else:
		numberOfMatches = int(len(playerList) / 2) 
		matchPairings = getTwoHeadedMatches(playerList)

	for i in range(numberOfMatches, 1, -1):  
		potentialPairings = getPotentialPairings(matchPairings, i)
		if potentialPairings:
			break

	averageDates = getAverageDates(potentialPairings)

	for idx,pairings in potentialPairings:
		if averageDates[idx] == max(averageDates):
			return pairings
			break


def getPotentialPairings(matchPairings, r):

	for pairings in permutations(matchPairings, r):
		allPlayers = flatten([x[1] for x in pairings])
		for player in allPlayers:
			if player not in seen:
				seen.append(player)
		if len(seen) == len(allPlayers):
			yield pairings


def getAverageDates(potentialPairings):

	for pairings in PotentialPairings:
		draftDates = [x[2] for x in pairings]
		averageDate = mean(draftDates)
		yield averageDate


def getMatches(playerList):

	sql = '''SELECT t.name, ep1.player_id, ep2.player_id, t.date
				FROM Match AS m
				INNER JOIN MatchParticipant AS mp1 ON m.id = mp1.match_id
				INNER JOIN MatchParticipant AS mp2 ON m.id = mp2.match_id AND mp.entity_id <> mp2.entity_id
				INNER JOIN entity AS e1 ON e1.id = mp1.entity_id
				INNER JOIN entity AS e2 ON e2.id = mp2.entity_id
				INNER JOIN entityParticipant AS ep1 ON ep1.entity_id = mp1.entity_id
				INNER JOIN entityParticipant AS ep2 ON ep2.entity_id = mp2.entity_id
				INNER JOIN Tournament AS t ON t.id = m.tournament_id
				INNER JOIN TournamentType AS tt on t.type = tt.id
				WHERE ep1.player_id IN (''' + ''', '''.join(playerList) + ''')
					AND ep2.player_id IN (''' + ''', '''.join(playerList) + ''')
					AND mp1.game_wins <> tt.game_wins.required
					AND mp2.game_wins <> tt.game_wins.required
					AND tt.description = 'Normal' '''

	results = db.session.execute(sql).fetchall()

	for row in results:
		matchList.append((row[0],[row[1],row[2]],row[5]))

	return matchList


def getTwoHeadedMatches(playerList):

	twoHeadedsql = '''SELECT t.name, ep1.player_id, ep2.player_id, ep3.player_id, ep4.player_id, t.date
				FROM Match AS m
				INNER JOIN MatchParticipant AS mp1 ON m.id = mp1.match_id
				INNER JOIN MatchParticipant AS mp2 ON m.id = mp2.match_id AND mp.entity_id <> mp2.entity_id
				INNER JOIN entityParticipant AS ep1 ON ep1.entity_id = mp.entity_id
				INNER JOIN entityParticipant AS ep2 ON ep2.entity_id = mp.entity_id AND ep2.player_id <> ep1.player_id
				INNER JOIN entityParticipant AS ep3 ON ep3.entity_id = mp2.entity_id
				INNER JOIN entityParticipant AS ep4 ON ep4.entity_id = mp2.entity_id AND ep4.player_id <> ep3.player_id
				INNER JOIN Tournament AS t ON t.id = m.tournament_id
				INNER JOIN TournamentType AS tt on t.type = tt.id
				WHERE ep1.player_id IN (''' + ''', '''.join(playerList) + ''')
					AND ep2.player_id IN (''' + ''', '''.join(playerList) + ''')
					AND ep3.player_id IN (''' + ''', '''.join(playerList) + ''')
					AND ep4.player_id IN (''' + ''', '''.join(playerList) + ''')
					AND mp1.game_wins <> tt.game_wins.required
					AND mp2.game_wins <> tt.game_wins.required
					AND tt.description = 'Two Headed Giant' '''

	results = db.session.execute(sql).fetchall()

	for row in results:
		matchList.append((row[0],[row[1],row[2],row[3],row[4]],row[5]))

	return matchList 


def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el






