import psycopg2, sqlite3
from app.api import *
import os
import urllib.parse as urlparse

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])

pgConn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

pgCursor = pgConn.cursor()

pgCursor.execute('DELETE FROM statistics')
pgCursor.execute('DELETE FROM match_participant')
pgCursor.execute('DELETE FROM entity_participant')
pgCursor.execute('DELETE FROM entity')
pgCursor.execute('DELETE FROM match')
pgCursor.execute('DELETE FROM tournament')
pgCursor.execute('DELETE FROM set')
pgCursor.execute('DELETE FROM player')
pgCursor.execute('DELETE FROM tournament_type')
pgConn.commit()

pgCursor.execute('ALTER SEQUENCE tournament_id_seq RESTART WITH 1')
pgConn.commit()

slConn = sqlite3.connect('app.db')
slCursor = slConn.cursor()

# Players
slCursor.execute('SELECT username, password, name, email FROM player')

for row in slCursor.fetchall():
	pgCursor.execute('INSERT INTO player (username, password, name, email) VALUES(%s, %s, %s, %s) RETURNING id', [row[0], row[1], row[2], row[3]])
	pgConn.commit()
	playerId = pgCursor.fetchone()[0]

	pgCursor.execute('INSERT INTO entity values(default) RETURNING id')
	pgConn.commit()
	entityId = pgCursor.fetchone()[0]

	pgCursor.execute('INSERT INTO entity_participant (entity_id, player_id) values(%s, %s)', [entityId, playerId])
	pgConn.commit()

# Tournaments
pgCursor.execute("INSERT INTO tournament_type (description) VALUES('Normal'), ('Two headed Giant')")
pgConn.commit()
pgCursor.execute("SELECT id FROM tournament_type WHERE description = 'Normal'")
normalTournament = pgCursor.fetchone()

slCursor.execute('SELECT name, date, id FROM tournament')

for row in slCursor.fetchall():
	pgCursor.execute('INSERT INTO tournament (name, date, type) VALUES(%s, %s, %s) RETURNING id', [row[0], row[1], normalTournament[0]])
	pgConn.commit()
	tournamentId = pgCursor.fetchone()[0]

	# Matches
	slCursor.execute('''SELECT t1.name, p1.username, p2.username, m1.game_wins, m2.game_wins
							FROM match AS m1
							INNER JOIN match AS m2 ON m1.tournament_id = m2.tournament_id
							INNER JOIN player AS p1 ON m1.player_id = p1.id
							INNER JOIN player AS p2 ON m2.player_id = p2.id
							INNER JOIN tournament AS t1 ON m1.tournament_id = t1.id
							AND m1.match_id = m2.match_id
							AND m1.player_id > m2.player_id
							WHERE t1.id = ?''', [row[2],])

	for row in slCursor.fetchall():

		pgCursor.execute('INSERT INTO match (tournament_id) VALUES(%s) RETURNING id', [tournamentId])
		pgConn.commit()
		matchId = pgCursor.fetchone()[0]

		pgCursor.execute('SELECT ep.entity_id FROM entity_participant AS ep INNER JOIN player AS p ON ep.player_id = p.id WHERE p.username = %s', [row[1],])
		entityId = pgCursor.fetchone()

		pgCursor.execute('INSERT INTO match_participant (match_id, entity_id, game_wins) VALUES(%s, %s, %s)', [matchId, entityId, row[3]])
		pgConn.commit()

		pgCursor.execute('SELECT entity_id FROM entity_participant AS ep INNER JOIN player AS p ON ep.player_id = p.id WHERE p.username = %s', [row[2],])
		entityId = pgCursor.fetchone()

		pgCursor.execute('INSERT INTO match_participant (match_id, entity_id, game_wins) VALUES(%s, %s, %s)', [matchId, entityId, row[4]])
			
		pgConn.commit()
		
		rebuildStatistics(tournamentId)	
