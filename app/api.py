from sqlalchemy import func, and_, extract, case
from sqlalchemy.sql import text
from datetime import date
from app.models import Player, Tournament, Match, Set, Statistics, TournamentType, Entity, EntityParticipant, MatchParticipant
import smtplib
import json
from itertools import combinations
from app.post import slack_bot

from app import db

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

def getTournamentResults(id):

	return Statistics.query.filter(Statistics.tournament_id == id).order_by(Statistics.match_wins.desc(), Statistics.game_win_percentage.desc()).all()

def addPositions(statistics):

	sortedList = sorted(statistics, key = lambda x: (x['match_win_percentage'], x['game_win_percentage']), reverse=True)
	
	position = 0
	savedPosition = 0
	savedMatchWinPercentage = 0
	savedGameWinPercentage = 0

	for player in sortedList:

		if player['match_win_percentage'] == savedMatchWinPercentage and player['game_win_percentage'] == savedGameWinPercentage:
			player['position'] = savedPosition
		else:
			savedPosition += 1
			player['position'] = savedPosition
			savedMatchWinPercentage = player['match_win_percentage']
			savedGameWinPercentage = player['game_win_percentage']	
	
	return sortedList
	
def getLifetimeStatistics():

	results = db.session.query(Entity, func.sum(Statistics.match_wins).label("total_match_wins"), 
								func.sum(Statistics.match_losses).label("total_match_losses"), 
		                    	func.sum(Statistics.game_wins).label("total_game_wins"), 
		                    	func.sum(Statistics.game_losses).label("total_game_losses")).join(Statistics).join(Tournament).join(TournamentType).filter(TournamentType.description == 'Normal').group_by(Entity.id).all()

	statistics = []
	for row in results:
		rowDictionary = {'total_match_wins':row.total_match_wins,
						 'total_match_losses':row.total_match_losses,
						 'total_game_wins':row.total_game_wins,
						 'total_game_losses':row.total_game_losses,		
			 			 'match_win_percentage':row.total_match_wins/(row.total_match_wins + row.total_match_losses) * 100 if (row.total_match_wins + row.total_match_losses) > 0 else 0.0,
						 'game_win_percentage':row.total_game_wins/(row.total_game_wins + row.total_game_losses) * 100 if (row.total_game_wins + row.total_game_losses) > 0 else 0.0,
						 'total_matches_played':row.total_match_wins + row.total_match_losses,
						 'player':row.Entity.participants[0].player.name}
		statistics.append(rowDictionary)

	return addPositions(statistics)

def getYearStatistics(year):

	results = db.session.query(Entity, func.sum(Statistics.match_wins).label("total_match_wins"), 
								func.sum(Statistics.match_losses).label("total_match_losses"), 
		                    	func.sum(Statistics.game_wins).label("total_game_wins"), 
		                    	func.sum(Statistics.game_losses).label("total_game_losses"),
							extract('YEAR', Tournament.date).label("year")).join(Statistics).join(Tournament).join(TournamentType).filter(extract('YEAR', Tournament.date) == year).filter(TournamentType.description == 'Normal').group_by(Entity.id, extract('YEAR', Tournament.date)).all()

	statistics = []
	for row in results:
		rowDictionary = {'total_match_wins':row.total_match_wins,
						 'total_match_losses':row.total_match_losses,
						 'total_game_wins':row.total_game_wins,
						 'total_game_losses':row.total_game_losses,		
			 			 'match_win_percentage':row.total_match_wins/(row.total_match_wins + row.total_match_losses) * 100 if (row.total_match_wins + row.total_match_losses) > 0 else 0.0,
						 'game_win_percentage':row.total_game_wins/(row.total_game_wins + row.total_game_losses) * 100 if (row.total_game_wins + row.total_game_losses) > 0 else 0.0,
						 'total_matches_played':row.total_match_wins + row.total_match_losses,
						 'player':row.Entity.participants[0].player.name,
						 'year':row.year}
		statistics.append(rowDictionary)	

	return addPositions(statistics)

def getSetStatistics(id):

	results = db.session.query(Entity, Set, func.sum(Statistics.match_wins).label("total_match_wins"), 
								func.sum(Statistics.match_losses).label("total_match_losses"), 
		                    	func.sum(Statistics.game_wins).label("total_game_wins"), 
		                    	func.sum(Statistics.game_losses).label("total_game_losses")).join(Statistics).join(Tournament).join(TournamentType).join(Set).filter(TournamentType.description == 'Normal').filter(Set.id == id).group_by(Entity.id, Set.id).all()

	statistics = []
	for row in results:
		rowDictionary = {'total_match_wins':row.total_match_wins,
						 'total_match_losses':row.total_match_losses,
						 'total_game_wins':row.total_game_wins,
						 'total_game_losses':row.total_game_losses,		
			 			 'match_win_percentage':row.total_match_wins/(row.total_match_wins + row.total_match_losses) * 100 if (row.total_match_wins + row.total_match_losses) > 0 else 0.0,
						 'game_win_percentage':row.total_game_wins/(row.total_game_wins + row.total_game_losses) * 100 if (row.total_game_wins + row.total_game_losses) > 0 else 0.0,
						 'total_matches_played':row.total_match_wins + row.total_match_losses,
						 'player':row.Entity.participants[0].player.name,
						 'set':row.Set.name}
		statistics.append(rowDictionary)	

	return addPositions(statistics)	

def getyearByYearStatistics():

	return [getYearStatistics(year) for year in reversed(db.session.query(extract('YEAR', Tournament.date) ).distinct().order_by(extract('YEAR', Tournament.date)).all())] 

def getStatisticsBySet():

	return [getSetStatistics(set.id) for set in Set.query.order_by(Set.name).all()] 

def getUnfinishedTournamentResults(id):

	return [getTournamentResults(tournament.id) for tournament in reversed(getTournaments()) if unfinishedMatchesInTournament(tournament.id)]

def getPlayerHeadToHeadData():

	sql = '''SELECT p1.name AS player, p2.name AS opponent, sum(CASE WHEN mp1.game_wins = tt.game_wins_required THEN 1 ELSE 0 END) AS total_match_wins, 
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
			GROUP BY ep1.entity_id, p1.name, ep2.entity_id, p2.name
			ORDER BY p1.name, p2.name'''
			
	return db.session.execute(sql).fetchall()

def rebuildStatistics(tournamentId):

	sql = '''DELETE FROM statistics WHERE tournament_id = ''' + str(tournamentId)

	db.session.execute(sql)
	db.session.execute(sql)

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

	for player in Statistics.query.filter(Statistics.tournament_id == tournamentId).order_by(Statistics.match_wins.desc(), Statistics.game_win_percentage.desc()).all():

		if player.match_wins == savedMatchWins and player.game_win_percentage == savedGameWinPercentage:
			player.position = savedPosition
		else:
			savedPosition += 1
			player.position = savedPosition
			savedMatchWins = player.match_wins
			savedGameWinPercentage = player.game_win_percentage

	db.session.commit()

	players = [player.entity.participants for player in Statistics.query.filter(Statistics.tournament_id == tournamentId).filter(Statistics.position == 1).all()]

	if players:
		winnerList = [player.player.name for player in players[0]]
		winnerString = ", ".join(winnerList)
		tournament = Tournament.query.filter(Tournament.id == tournamentId).first()
		tournament.winners = winnerString
		db.session.commit()

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

	if not unfinishedMatchesInTournament(matchId):
		slackResults(matchId)


############################################################
# Player APIs
############################################################
def usernameAlreadyTaken(username):

	return Player.query.filter(func.upper(Player.username) == username.upper()).first()

def createPlayer(name, email, password, username):

	if not name or not password or not username:
		raise ValueError('Invalid input when creating a new player')

	player = Player(name = name, email = email, password = password, username = username)	
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

def updatePlayer(id, name, email):

	if not playerExists(id):
		raise ValueError('Player does not exist')	

	player = getPlayer(id)

	player.name = name
	player.email = email
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

############################################################
# Set APIs
############################################################
def getSets():

	return Set.query.order_by(Set.id).all()

def getSet(id):

	if not setExists(id):
		raise ValueError('Set does not exist')

	return Set.query.filter(Set.id == id).first()

def createSet(name):

	if not name:
		raise ValueError('A set name must be supplied')

	db.session.add(Set(name = name))
	db.session.commit()

def updateSet(id, name):

	if not setExists(id):
		raise ValueError('Set does not exist')

	set = getSet(id)
	set.name = name
	db.session.commit()

def setExists(id):

	return Set.query.filter(Set.id == id).first() is not None

#############################################
# Email Results
############################################# 
def emailResults(id):

	GMAIL_USERNAME = 'jhcmagictournaments@gmail.com'
	GMAIL_PASSWORD = 'jhcmagicpassword'

	tournament = getTournamentResults(id)
	email_subject = tournament.name + ' Results'
	recipient_list = ', '.join([str(player.email) for player in Player.query.filter(Player.email != None).all()])

	body_of_email = render_template("email_results.html", tournament=tournament)

	session = smtplib.SMTP('smtp.gmail.com', 587)
	session.ehlo()
	session.starttls()
	session.login(GMAIL_USERNAME, GMAIL_PASSWORD)

	headers = "\r\n".join(["from: " + GMAIL_USERNAME,
	                       "subject: " + email_subject,
	                       "to: " + recipient_list,
	                       "mime-version: 1.0",
	                       "content-type: text/html"])
              
	content = headers + "\r\n\r\n" + body_of_email

	session.sendmail(GMAIL_USERNAME, recipients, content)

#############################################
# Post to Slack
############################################# 
def slackResults(id):

	with open('app/results.settings') as config:
		settings = json.loads(config.read())

	results_bot = slack_bot(self.settings['results_channel_url'], self.settings['results_channel_name'], self.settings['results_bot_name'], self.settings['results_bot_icon'], live)

	tournament = getTournamentResults(id)

	title = tournament.name + ' Results'
	for row in tournament:
		for idx, player in enumerate(row.entity.participants):
			if idx > 1:
				outPlayers += ' & '
			outPlayers += player.player.name
		outPlayers += '\n'

		outPosition += '{!s}\n'.format(row.Position)
		outMatchWins += '{!s}\n'.format(row.match_wins)
		outMatchLosses += '{!s}\n'.format(row.match_losses)
		outGameWins += '{!s}\n'.format(row.game_wins)
		outGameLosses += '{!s}\n'.format(row.game_losses)
		outPercentage += '{!s}\n'.format(row.game_win_percentage)


	post_results_message(title, outPlayers, outPosition, outMatchWins, outMatchLosses, outGameWins, outGameLosses, outPercentage)

