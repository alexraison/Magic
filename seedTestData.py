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

players = [(1,'test1', 'password', 'test 1', 'test1@test.com'),
		  (2,'test2', 'password', 'test 2', 'test2@test.com'),
		  (3,'test3', 'password', 'test 3', 'test3@test.com'),
		  (4,'test4', 'password', 'test 4', 'test4@test.com')]

pgCursor.executemany('INSERT INTO player (id, username, password, name, email) VALUES(%s,%s,%s,%s,%s)', players)
pgConn.commit()


entities = [(1,),
			(2,),
			(3,),
			(4,)]

#args_str = ','.join(pgCursor.mogrify('(%s)', x) for x in entities)
pgCursor.executemany('INSERT INTO Entity (id) VALUES(%s)', entities)
pgConn.commit()


entityparticipants = [(1,1),
					  (2,2),
					  (3,3),
					  (4,4)]


#args_str = ','.join(pgCursor.mogrify('(%s,%s)', x) for x in entityparticipants)
pgCursor.executemany('INSERT INTO Entity_Participant (entity_id, player_id) VALUES(%s,%s)', entityparticipants)
pgConn.commit()


tournamenttypes = [(1,'test', 2),
				   (2,'test2',2)]

#args_str = ','.join(pgCursor.mogrify('(%s,%s,%s)', x) for x in tournamenttypes)
pgCursor.executemany('INSERT INTO Tournament_Type (id, description, game_wins_required) VALUES(%s,%s,%s)', tournamenttypes)
pgConn.commit()


sets = [1,'test']

#args_str = ','.join(pgCursor.mogrify('(%s,%s)', x) for x in tournamenttypes)
pgCursor.execute('INSERT INTO Set (id, name) VALUES(%s,%s)', sets)
pgConn.commit()


tournaments = [1,'tournament1', '1', '1', 20160223]

#args_str = ','.join(pgCursor.mogrify('(%s,%s,%s,%s,%s)', x) for x in tournaments)
pgCursor.execute('INSERT INTO Tournament (id, name, type, set_id, date) VALUES(%s,%s,%s,%s,%s)', tournaments)
pgConn.commit()


matches = [(1,1),
		   (1,1)]

#args_str = ','.join(pgCursor.mogrify('(%s,%s)', x) for x in matches)
pgCursor.executemany('INSERT INTO Match (tournament_id, match_id) VALUES(%s,%s)', matches)
pgConn.commit()


matchparticipants = [(1,1,0),
					 (1,2,0)]

#args_str = ','.join(pgCursor.mogrify('(%s,%s,%s)', x) for x in matchparticipants)
pgCursor.executemany('INSERT INTO Match_Participant (match_id, entity_id, game_wins) VALUES(%s,%s,%s)', matchparticipants)
pgConn.commit()