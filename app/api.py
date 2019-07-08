from sqlalchemy import func, and_, extract, case
from sqlalchemy.sql import text
from datetime import date
from app.models import Player, Tournament, Match, Set, Statistics, TournamentType, Entity, EntityParticipant, MatchParticipant
import smtplib
import json
from itertools import combinations
from app.post import slack_bot
import os

from app import app, db

############################################################
# Type APIs
############################################################
def getTypeFromLiteral(typeLiteral):

	if typeLiteral == 'NORMAL':
		type = TournamentType.query.filter(TournamentType.description == 'Normal').first()


	if typeLiteral == 'TWOHEADEDGIANT':
		type = TournamentType.query.filter(TournamentType.description == 'Two Headed Giant').first()

	return type.id

############################################################
# Tournament APIs
############################################################
def getTournaments():

	return Tournament.query.order_by(Tournament.id.desc()).all()

def getTournament(id):

	return Tournament.query.filter(Tournament.id == id).first()

def getTournamentName(id):

	tournament = getTournament(id)

	return tournament.name

def updateTournament(id, name, set):

	tournament = getTournament(id)
	tournament.name = name
	tournament.set_id = set
	db.session.commit()

def createTournament(name, set, entities, typeLiteral):

	type = getTypeFromLiteral(typeLiteral)

	newTournament = Tournament(name = name, set_id = set, date = date.today(), type = type)
	db.session.add(newTournament)
	db.session.commit()

	for idx, pairing in enumerate(combinations(entities, 2)):

		newMatch = Match(tournament_id = newTournament.id)
		db.session.add(newMatch)
		db.session.commit()

		db.session.add(MatchParticipant(match_id = newMatch.id, entity_id = pairing[0], game_wins = 0))
		db.session.add(MatchParticipant(match_id = newMatch.id, entity_id = pairing[1], game_wins = 0))
		db.session.commit()

	rebuildStatistics(newTournament.id)

def createTournamentType(description,gameWinsRequired):
	newTournamentType = TournamentType(description = description, game_wins_required = gameWinsRequired)
	db.session.add(newTournamentType)
	db.session.commit()

def getTournamentResults(id):

	return Statistics.query.filter(Statistics.tournament_id == id).order_by(Statistics.match_wins.desc(), Statistics.game_win_percentage.desc(), Statistics.game_losses.asc()).all()

def addPositions(statistics):

	sortedList = sorted(statistics, key = lambda x: (x['match_win_percentage'], x['game_win_percentage']), reverse=True)
	
	position = 0
	savedPosition = 0
	savedMatchWinPercentage = 0
	savedGameWinPercentage = 0

	for idx, player in enumerate(sortedList):

		if player['match_win_percentage'] == savedMatchWinPercentage and player['game_win_percentage'] == savedGameWinPercentage:
			player['position'] = savedPosition
		else:		
			player['position'] = idx + 1
			savedPosition = idx + 1
			savedMatchWinPercentage = player['match_win_percentage']
			savedGameWinPercentage = player['game_win_percentage']	
	
	return sortedList
	
def getLifetimeStatistics(formats):

	if formats == 'limited' or formats == 'constructed':
		constructedBoolean = (formats == 'constructed')
		results = db.session.query(Entity, func.sum(Statistics.match_wins).label("total_match_wins"), 
									func.sum(Statistics.match_losses).label("total_match_losses"), 
			                    	func.sum(Statistics.game_wins).label("total_game_wins"), 
			                    	func.sum(Statistics.game_losses).label("total_game_losses")).join(Statistics).join(Tournament).join(TournamentType).join(Set).filter(TournamentType.description == 'Normal').filter(Set.constructed == constructedBoolean).group_by(Entity.id).all()

		tournaments = db.session.query(Entity, Tournament.id).join(Statistics).join(Tournament).join(TournamentType).join(Set).filter(Statistics.position == 1).filter(TournamentType.description == 'Normal').filter(Set.constructed == constructedBoolean).all()

	else:
		results = db.session.query(Entity, func.sum(Statistics.match_wins).label("total_match_wins"), 
									func.sum(Statistics.match_losses).label("total_match_losses"), 
			                    	func.sum(Statistics.game_wins).label("total_game_wins"), 
			                    	func.sum(Statistics.game_losses).label("total_game_losses")).join(Statistics).join(Tournament).join(TournamentType).filter(TournamentType.description == 'Normal').group_by(Entity.id).all()
		
		tournaments = db.session.query(Entity, Tournament.id).join(Statistics).join(Tournament).join(TournamentType).filter(Statistics.position == 1).filter(TournamentType.description == 'Normal').all()

	statistics = []
	for row in results:

		wins = 0
		for tournament in tournaments:
			if row.Entity == tournament[0] and not unfinishedMatchesInTournament(tournament[1]):
				wins += 1

		rowDictionary = {'total_match_wins':row.total_match_wins,
						 'total_match_losses':row.total_match_losses,
						 'total_game_wins':row.total_game_wins,
						 'total_game_losses':row.total_game_losses,		
			 			 'match_win_percentage':row.total_match_wins/(row.total_match_wins + row.total_match_losses) * 100 if (row.total_match_wins + row.total_match_losses) > 0 else 0.0,
						 'game_win_percentage':row.total_game_wins/(row.total_game_wins + row.total_game_losses) * 100 if (row.total_game_wins + row.total_game_losses) > 0 else 0.0,
						 'total_matches_played':row.total_match_wins + row.total_match_losses,
						 'player':row.Entity.participants[0].player.name,
						 'tournament_wins':wins}
		statistics.append(rowDictionary)

	return addPositions(statistics)

def getYearStatistics(year):

	results = db.session.query(Entity, func.sum(Statistics.match_wins).label("total_match_wins"), 
								func.sum(Statistics.match_losses).label("total_match_losses"), 
		                    	func.sum(Statistics.game_wins).label("total_game_wins"), 
		                    	func.sum(Statistics.game_losses).label("total_game_losses"),               	
							extract('YEAR', Tournament.date).label("year")).join(Statistics).join(Tournament).join(TournamentType).filter(extract('YEAR', Tournament.date) == year).filter(TournamentType.description == 'Normal').group_by(Entity.id, extract('YEAR', Tournament.date)).all()

	tournaments = db.session.query(Entity, Tournament.id).join(Statistics).join(Tournament).join(TournamentType).filter(Statistics.position == 1).filter(extract('YEAR', Tournament.date) == year).filter(TournamentType.description == 'Normal').all()

	statistics = []
	for row in results:

		wins = 0
		for tournament in tournaments:
			if row.Entity == tournament[0] and not unfinishedMatchesInTournament(tournament[1]):
				wins += 1

		rowDictionary = {'total_match_wins':row.total_match_wins,
						 'total_match_losses':row.total_match_losses,
						 'total_game_wins':row.total_game_wins,
						 'total_game_losses':row.total_game_losses,		
			 			 'match_win_percentage':row.total_match_wins/(row.total_match_wins + row.total_match_losses) * 100 if (row.total_match_wins + row.total_match_losses) > 0 else 0.0,
						 'game_win_percentage':row.total_game_wins/(row.total_game_wins + row.total_game_losses) * 100 if (row.total_game_wins + row.total_game_losses) > 0 else 0.0,
						 'total_matches_played':row.total_match_wins + row.total_match_losses,
						 'player':row.Entity.participants[0].player.name,
						 'year':row.year,
						 'tournament_wins':wins}
		statistics.append(rowDictionary)	

	return addPositions(statistics)

def getSetStatistics(id):

	results = db.session.query(Entity, Set, func.sum(Statistics.match_wins).label("total_match_wins"), 
								func.sum(Statistics.match_losses).label("total_match_losses"), 
		                    	func.sum(Statistics.game_wins).label("total_game_wins"), 
		                    	func.sum(Statistics.game_losses).label("total_game_losses")).join(Statistics).join(Tournament).join(TournamentType).join(Set).filter(TournamentType.description == 'Normal').filter(Set.id == id).group_by(Entity.id, Set.id).all()

	tournaments = db.session.query(Entity, Tournament.id).join(Statistics).join(Tournament).join(TournamentType).join(Set).filter(Statistics.position == 1).filter(Statistics.matches_unfinished == 0).filter(TournamentType.description == 'Normal').filter(Set.id == id).all()

	statistics = []
	for row in results:

		wins = 0
		for tournament in tournaments:
			if row.Entity == tournament[0] and not unfinishedMatchesInTournament(tournament[1]):
				wins += 1

		rowDictionary = {'total_match_wins':row.total_match_wins,
						 'total_match_losses':row.total_match_losses,
						 'total_game_wins':row.total_game_wins,
						 'total_game_losses':row.total_game_losses,		
			 			 'match_win_percentage':row.total_match_wins/(row.total_match_wins + row.total_match_losses) * 100 if (row.total_match_wins + row.total_match_losses) > 0 else 0.0,
						 'game_win_percentage':row.total_game_wins/(row.total_game_wins + row.total_game_losses) * 100 if (row.total_game_wins + row.total_game_losses) > 0 else 0.0,
						 'total_matches_played':row.total_match_wins + row.total_match_losses,
						 'player':row.Entity.participants[0].player.name,
						 'set':row.Set.name,
						 'tournament_wins':wins}
		statistics.append(rowDictionary)	

	return addPositions(statistics)	

def getyearByYearStatistics():

	return [getYearStatistics(year) for year in reversed(db.session.query(extract('YEAR', Tournament.date) ).distinct().order_by(extract('YEAR', Tournament.date)).all())] 

def getStatisticsBySet():

	return [getSetStatistics(set.id) for set in Set.query.order_by(Set.name).all()] 

def getUnfinishedTournamentResults(id):

	return [getTournamentResults(tournament.id) for tournament in reversed(getTournaments()) if unfinishedMatchesInTournament(tournament.id)]

def getPlayerHeadToHeadData():

	sql = '''SELECT t.player AS player, t.opponent AS opponent, t.total_match_wins AS total_match_wins, t.total_match_losses AS total_match_losses, 
					t.total_game_wins AS total_game_wins, t.total_game_losses AS total_game_losses, t.total_matches_played AS total_matches_played, 
					CASE WHEN t.total_matches_played = 0 THEN 0 ELSE (CAST(t.total_match_wins AS decimal)/cast(t.total_matches_played AS decimal))*100 END AS match_win_percentage
			 FROM 
			(SELECT p1.name AS player, p2.name AS opponent, sum(CASE WHEN mp1.game_wins = tt.game_wins_required THEN 1 ELSE 0 END) AS total_match_wins, 
	                sum(CASE WHEN mp2.game_wins = tt.game_wins_required THEN 1 ELSE 0 END) AS total_match_losses, sum(mp1.game_wins) AS total_game_wins, 
					sum(mp2.game_wins) AS total_game_losses, sum(CASE WHEN mp1.game_wins = tt.game_wins_required THEN 1 ELSE 0 END) + sum(CASE WHEN mp2.game_wins = tt.game_wins_required THEN 1 ELSE 0 END) AS total_matches_played
			  FROM match AS m
			    INNER JOIN tournament AS t ON m.tournament_id = t.id
			    INNER JOIN tournament_type AS tt ON t.type = tt.id
			    INNER JOIN match_participant AS mp1 ON m.id = mp1.match_id
			    INNER JOIN entity_participant AS ep1 ON mp1.entity_id = ep1.entity_id
			    INNER JOIN player AS p1 ON ep1.player_id = p1.id
			    INNER JOIN match_participant AS mp2 ON m.id = mp2.match_id
			    INNER JOIN entity_participant AS ep2 ON mp2.entity_id = ep2.entity_id AND ep1.entity_id <> ep2.entity_id
			    INNER JOIN player AS p2 ON ep2.player_id = p2.id    
			WHERE tt.description = 'Normal' 
			GROUP BY ep1.entity_id, p1.name, ep2.entity_id, p2.name) AS t
			ORDER BY match_win_percentage DESC'''
			
	return db.session.execute(sql).fetchall()

def rebuildStatistics(tournamentId):

	sql = '''DELETE FROM statistics WHERE tournament_id = ''' + str(tournamentId)

	db.session.execute(sql)
	db.session.commit()

	sql = '''INSERT INTO statistics (tournament_id, entity_id, game_wins, game_losses, match_wins, match_losses, matches_unfinished)
				SELECT m.tournament_id, mp.entity_id, 
					       sum(mp.game_wins) AS total_game_wins, 
					       COALESCE(sum(mp3.game_wins), 0) AS total_game_losses,
					       sum(CASE WHEN mp.game_wins = tt.game_wins_required THEN 1 ELSE 0 END) AS match_wins, 
					       COALESCE(count(mp2.*), 0) AS match_losses, 
					       COALESCE(count(mp3.*) - count(mp2.*) - sum(CASE WHEN mp.game_wins = tt.game_wins_required THEN 1 ELSE 0 END), 0) AS matches_unfinished

					FROM match_participant AS mp
					  INNER JOIN match AS m ON mp.match_id = m.id
					  INNER JOIN tournament AS t ON m.tournament_id = t.id
					  INNER JOIN tournament_type AS tt ON t.type = tt.id
					  LEFT OUTER JOIN match_participant AS mp2 ON m.id = mp2.match_id AND mp.entity_id <> mp2.entity_id AND mp2.game_wins = tt.game_wins_required
					  LEFT OUTER JOIN match_participant AS mp3 ON m.id = mp3.match_id AND mp.entity_id <> mp3.entity_id

					WHERE m.tournament_id = ''' + str(tournamentId) + '''GROUP BY m.tournament_id, mp.entity_id'''

	db.session.execute(sql)
	db.session.commit()

	for player in Statistics.query.filter(Statistics.tournament_id == tournamentId).order_by(Statistics.match_wins.desc(), Statistics.game_win_percentage.desc()).all():
		player.match_win_percentage = player.match_wins/(player.match_wins + player.match_losses) * 100 if (player.match_wins + player.match_losses) > 0 else 0
		player.game_win_percentage = player.game_wins/(player.game_wins + player.game_losses) * 100 if (player.game_wins + player.game_losses) > 0 else 0
	db.session.commit()

	position = 0
	savedPosition = 0
	savedMatchWins = 0
	savedGameWinPercentage = 0

	for idx, player in enumerate(Statistics.query.filter(Statistics.tournament_id == tournamentId).order_by(Statistics.match_wins.desc(), Statistics.game_win_percentage.desc()).all()):

		if player.match_wins == savedMatchWins and player.game_win_percentage == savedGameWinPercentage:
			player.position = savedPosition
		else:
			player.position = idx + 1
			savedPosition = idx + 1
			savedMatchWins = player.match_wins
			savedGameWinPercentage = player.game_win_percentage

	db.session.commit()

	players = [player.entity.participants for player in Statistics.query.filter(Statistics.tournament_id == tournamentId).filter(Statistics.position == 1).all()]

	if players:
		winnerList = []
		for i in players:
			winnerList += [player.player.name for player in i]
		winnerString = ", ".join(winnerList)
		tournament = Tournament.query.filter(Tournament.id == tournamentId).first()
		tournament.winners = winnerString
		db.session.commit()

def removeParticipantFromTournament(tournamentId, entityId):
	
	if MatchParticipant.query.join(Match).join(Tournament).filter(Tournament.id == tournamentId).count() > 2:
		subQuery = db.session.query(MatchParticipant.match_id).filter(MatchParticipant.entity_id == entityId).subquery()
		matches = db.session.query(Match).filter(Match.id.in_(subQuery)).filter(Match.tournament_id == tournamentId).all()

		for match in matches:
			db.session.delete(match)

	else:
		tournament = db.session.query(Tournament).filter(Tournament.id == tournamentId).first()
		db.session.delete(tournament)

	db.session.commit()
 
	rebuildStatistics(tournamentId)

############################################################
# Match APIs
############################################################
def getOutstandingMatches():

	subQuery = db.session.query(MatchParticipant.match_id).join(Match).join(Tournament).join(TournamentType).filter(MatchParticipant.game_wins == TournamentType.game_wins_required).subquery()

	return Match.query.filter(~Match.id.in_(subQuery)).order_by(Match.tournament_id).all()

def getTournamentMatches(id):

	return Match.query.filter(Match.tournament_id == id).order_by(Match.tournament_id, Match.id).all()

def unfinishedMatchesInTournament(id):

	return Statistics.query.filter(Statistics.matches_unfinished > 0).filter(Statistics.tournament_id == id).first() is not None

def updateMatchResult(matchId, entityResults):

	match = Match.query.filter(Match.id == matchId).first()

	for result in entityResults:

		if result['gameWins'] > match.tournament.tournamentType.game_wins_required or result['gameWins'] < 0:
			raise ValueError('Invalid number of game wins')

		matchParticipant = MatchParticipant.query.filter(MatchParticipant.match_id == matchId).filter(MatchParticipant.entity_id == result['entityId']).first()
		matchParticipant.game_wins = result['gameWins']

	db.session.commit()

	rebuildStatistics(matchParticipant.matches.tournament.id)

	if not unfinishedMatchesInTournament(matchParticipant.matches.tournament.id):
		slackResults(matchParticipant.matches.tournament.id)


############################################################
# Player APIs
############################################################
def usernameAlreadyTaken(username):

	return Player.query.filter(func.upper(Player.username) == username.upper()).first()

def createPlayer(name, slackUser, password, username):

	if not name or not password or not username:
		raise ValueError('Invalid input when creating a new player')

	player = Player(name = name, slack_user = slackUser, password = password, username = username)	
	db.session.add(player)
	db.session.commit()

	entity = Entity()
	db.session.add(entity)
	db.session.commit()
	
	entityParticipant = EntityParticipant(entity_id = entity.id, player_id = player.id)
	db.session.add(entityParticipant)
	db.session.commit()	
	
def playerExists(id):

	return Player.query.filter(Player.id == id).first() is not None

def updatePlayer(id, name, slackUser):

	if not playerExists(id):
		raise ValueError('Player does not exist')	

	player = getPlayer(id)

	player.name = name
	player.slack_user = slackUser
	db.session.commit()

def getPlayers():

	return Player.query.order_by(Player.name).all()
	
def getPlayer(id):

	if not playerExists(id):
		raise ValueError('Player does not exist')	

	return Player.query.filter(Player.id == id).first()

def getCurrentPlayer(username):

	return Player.query.filter(func.upper(Player.username) == username.upper()).first()

def pairAlreadyExists(players):

	# Please don't yell at me, it's late
	sql = '''SELECT e.id FROM entity AS e 
				INNER JOIN entity_participant AS ep1 ON e.id = ep1.entity_id 
				INNER JOIN entity_participant AS ep2 ON e.id = ep2.entity_id 
				WHERE ep1.player_id = ''' 
	sql = sql + str(players[0]) + " AND ep2.player_id = " + str(players[1])
	sql = sql + " AND e.id IN (SELECT entity_id FROM entity_participant GROUP BY entity_id HAVING count(*) = 2) GROUP BY e.id"

	return db.session.execute(sql).fetchone() is not None

def createPair(players):

	entity = Entity()
	db.session.add(entity)
	db.session.commit()

	for player in players:
		db.session.add(EntityParticipant(entity_id = entity.id, player_id = player))

	db.session.commit()

def getPlayerNamesFromSlackUsers(slackUsers):

	playerList = []

	sql = """SELECT p.name FROM player AS p
				WHERE p.slack_user IN ('""" + "', '".join(slackUsers) + """')"""

	results = db.session.execute(sql).fetchall()

	for row in results:
		playerList.append(row[0])

	return playerList 


############################################################
# Set APIs
############################################################
def getSets():

	return Set.query.order_by(Set.id).all()

def getSet(id):

	if not setExists(id):
		raise ValueError('Set does not exist')

	return Set.query.filter(Set.id == id).first()

def createSet(name, constructed):

	if not name:
		raise ValueError('A set name must be supplied')

	db.session.add(Set(name = name, constructed = constructed))
	db.session.commit()

def updateSet(id, name, constructed):

	if not setExists(id):
		raise ValueError('Set does not exist')

	set = getSet(id)
	set.name = name
	set.constructed = constructed
	db.session.commit()

def setExists(id):

	return Set.query.filter(Set.id == id).first() is not None

#############################################
# Post to Slack
############################################# 
def slackResults(id):

	
	with open('app/results.settings') as config:
		settings = json.loads(config.read())

	if app.config['TESTING'] == True:
		channel = os.environ['TESTING_CHANNEL_ID']
	else:
		channel = os.environ['CHANNEL_ID']
	results_bot = slack_bot(channel, settings['bot_name'], settings['bot_icon'])

	tournament = getTournamentResults(id)

	outPlayers = ''
	outMatchWins = ''
	outPercentage = ''

	tournamentName = getTournamentName(id)

	title = tournamentName + ' Results'
	for row in tournament:
		outPlayers = ''
		for idx, player in enumerate(row.entity.participants):
			if idx > 0:
				outPlayers += ' & '
			outPlayers += player.player.name

		print(str(row.position) + ' ' + outPlayers)

		outPercentage += '{!s}.\t{!s}%\n'.format(row.position, round(row.game_win_percentage,1))
		outMatchWins += '{!s}. {!s} :   {!s} / {!s}\n'.format(row.position, outPlayers, row.match_wins, row.match_losses)

	attachment = {
			'title': title,
            'fields': [
                {
                    'title': "Match Wins/Losses",
                    'value': outMatchWins,
                    'short': "true"
                },
                {
                    'title': "Game Win %",
                    'value': outPercentage,
                    'short': "true"
                }               
            ],
            'color': "#F35A00"
        }

	results_bot.post_attachment(attachment)

def getMovingAverages():

	sql = '''SELECT * FROM (
				SELECT data.player, data.year, data.quarter,  
				       AVG(data.match_win_percentage)
				            OVER(ORDER BY data.player, data.year, data.quarter ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) AS average_match_win_percentage
				FROM ( 
				SELECT EXTRACT(YEAR FROM series) AS year, EXTRACT(QUARTER FROM series) AS quarter, play1.name AS player, b.match_win_percentage

				FROM player AS play1
				  CROSS JOIN generate_series('2011-01-01  00:00', now(), interval '3 months') AS series
				  LEFT JOIN (
				    SELECT a.player AS player,
				        a.year,
				        a.quarter,
				        CASE WHEN SUM(a.total_matches_played) = 0 THEN 0 ELSE (CAST(SUM(a.total_match_wins) AS decimal)/cast(SUM(a.total_matches_played) AS decimal))*100 END AS match_win_percentage  
				    FROM
				    (SELECT p1.name AS player, sum(CASE WHEN mp1.game_wins = tt.game_wins_required THEN 1 ELSE 0 END) AS total_match_wins, 
				            sum(CASE WHEN mp2.game_wins = tt.game_wins_required THEN 1 ELSE 0 END) AS total_match_losses, 
				            sum(CASE WHEN mp1.game_wins = tt.game_wins_required THEN 1 ELSE 0 END) + sum(CASE WHEN mp2.game_wins = tt.game_wins_required THEN 1 ELSE 0 END) AS total_matches_played,
				            t.date,
				            EXTRACT(QUARTER FROM t.date) AS quarter,
				            EXTRACT(YEAR FROM t.date) AS year
				    FROM match AS m
				        INNER JOIN tournament AS t ON m.tournament_id = t.id
				        INNER JOIN tournament_type AS tt ON t.type = tt.id
				        INNER JOIN match_participant AS mp1 ON m.id = mp1.match_id
				        INNER JOIN entity_participant AS ep1 ON mp1.entity_id = ep1.entity_id
				        INNER JOIN match_participant AS mp2 ON m.id = mp2.match_id AND mp1.entity_id <> mp2.entity_id
				        INNER JOIN entity_participant AS ep2 ON mp2.entity_id = ep2.entity_id 
				        INNER JOIN player AS p1 ON ep1.player_id = p1.id
				    WHERE tt.description = 'Normal' 
				    GROUP BY ep1.entity_id, p1.name, ep2.entity_id, t.date) AS a
				    GROUP BY a.player, a.year, a.quarter) AS b 
				    ON EXTRACT(YEAR FROM series) = b.year AND EXTRACT(QUARTER FROM series) = b.quarter AND play1.name = b.player
				ORDER BY play1.name, year, quarter  ) AS data ) AS data2
				WHERE NOT (data2.year = 2011 AND data2.quarter = 3)
                  AND NOT (data2.year = 2011 AND data2.quarter = 2)
                  AND NOT (data2.year = 2011 AND data2.quarter = 1)'''

	return db.session.execute(sql).fetchall()				