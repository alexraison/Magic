from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask_sslify import SSLify
import os
import threading

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
sslify = SSLify(app, permanent=True)

db = SQLAlchemy(app)

def playerInParticipantOne(currentPlayer, match):
	for participant in match.participants[1].entity.participants:
		if currentPlayer == participant.player:
			return True
	return False

app.jinja_env.globals.update(playerInParticipantOne=playerInParticipantOne)

from app import views, models

from app.automatedPairings import *
threading.Thread(target=scheduledPairings, name='PAIRINGS').start()