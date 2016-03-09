from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
print(os.environ)
db = SQLAlchemy(app)

def playerInParticipantOne(currentPlayer, match):
	for participant in match.participants[1].entity.participants:
		if currentPlayer == participant.player:
			return True
	return False

app.jinja_env.globals.update(playerInParticipantOne=playerInParticipantOne)

from app import views, models