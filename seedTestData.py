import psycopg2
from app.api import *
import os
import urllib.parse as urlparse

from app import db

db.create_all()

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

players = [('test1', 'password', 'test 1', 'test1@test.com'),
		  ('test2', 'password', 'test 2', 'test2@test.com'),
		  ('test3', 'password', 'test 3', 'test3@test.com'),
		  ('test4', 'password', 'test 4', 'test4@test.com'),
		  ('test5', 'password', 'test 5', 'test1@test.com'),
		  ('test6', 'password', 'test 6', 'test2@test.com'),
		  ('test7', 'password', 'test 7', 'test3@test.com'),
		  ('test8', 'password', 'test 8', 'test4@test.com')]

pgCursor.executemany('INSERT INTO player (username, password, name, email) VALUES(%s,%s,%s,%s)', players)
pgConn.commit()

for i in range(8):
	pgCursor.execute('INSERT INTO Entity (id) values(default)')
	pgConn.commit()

entityparticipants = [(1,1),
					  (2,2),
					  (3,3),
					  (4,4),
					  (5,5),
					  (6,6),
					  (7,7),
					  (8,8)]

pgCursor.executemany('INSERT INTO Entity_Participant (entity_id, player_id) VALUES(%s,%s)', entityparticipants)
pgConn.commit()

tournamenttypes = [('Normal', 2),
				   ('Normal', 2)]

pgCursor.executemany('INSERT INTO Tournament_Type (description, game_wins_required) VALUES(%s,%s)', tournamenttypes)

sets = ['test']

pgCursor.execute('INSERT INTO Set (name) VALUES(%s)', sets)
pgConn.commit()

tournaments = ['tournament1', 1, 1, '2016-02-23']

pgCursor.execute('INSERT INTO Tournament (name, type, set_id, date) VALUES(%s,%s,%s,%s)', tournaments)
pgConn.commit()

matches = [1,]

pgCursor.execute('INSERT INTO Match (tournament_id) VALUES(%s)', matches)
pgConn.commit()


matchparticipants = [(1,1,0),
					 (1,2,0)]


pgCursor.executemany('INSERT INTO Match_Participant (match_id, entity_id, game_wins) VALUES(%s,%s,%s)', matchparticipants)
pgConn.commit()