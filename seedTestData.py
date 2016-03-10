import psycopg2
from app.api import *
import os
import urllib.parse as urlparse

from app import db

db.create_all()

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])

createPlayer('Peter Parker', 'test1@email.com', 'password', 'test1')
createPlayer('Matthew Murdock', 'test2@email.com', 'password', 'test2')
createPlayer('Ziggy Stardust', 'test3@email.com', 'password', 'test3')
createPlayer('Morrissey', 'test4@email.com', 'password', 'test4')
createPlayer('Darth Vader', 'test5@email.com', 'password', 'test5')
createPlayer('Johnny Marr', 'test6@email.com', 'password', 'test6')
createPlayer('Damon Albarn', 'test7@email.com', 'password', 'test7')
createPlayer('Mike', 'test8@email.com', 'password', 'test8')
createPlayer('Thin White Duke', 'test9@email.com', 'password', 'test9')
createPlayer('Carl the Nampire', 'test10@email.com', 'password', 'test10')

createPair([1,2])
createPair([3,4])
createPair([5,6])
createPair([7,8])
createPair([9,10])

createTournamentType('Normal',2)
createTournamentType('Two Headed Giant',1)

createSet('Test Set 1')
createSet('Test Set 2')
createSet('Test Set 3')

createTournament('Tournament 1', 1, [1,2,3,4,5,6,7,8,9,10], 'NORMAL')
createTournament('Tournament 2', 2, [1,2,5,6,7,10], 'NORMAL')
createTournament('Tournament 3', 3, [1,2,3,4,5,6,7,8,9,10], 'NORMAL')
createTournament('Tournament 4', 1, [9,10], 'NORMAL')
createTournament('2HG Tournament 1', 3, [11,12,13,14,15], 'TWOHEADEDGIANT')
createTournament('2HG Tournament 2', 1, [11,13,15], 'TWOHEADEDGIANT')
