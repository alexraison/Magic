import psycopg2
from app.api import *
import os
import urllib.parse as urlparse

from app import db

db.create_all()

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])

createPlayer('Peter Parker', 'slack', 'password', 'test1')
createPlayer('Matthew Murdock', 'slack2', 'password', 'test2')
createPlayer('Ziggy Stardust', 'slack3', 'password', 'test3')
createPlayer('Morrissey', 'slack4', 'password', 'test4')
createPlayer('Darth Vader', 'slack5', 'password', 'test5')
createPlayer('Johnny Marr', 'slack6', 'password', 'test6')
createPlayer('Damon Albarn', 'slack7', 'password', 'test7')
createPlayer('Mike', 'slack8', 'password', 'test8')
createPlayer('Thin White Duke', 'slack9', 'password', 'test9')
createPlayer('Carl the Nampire', 'slack10', 'password', 'test10')

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
