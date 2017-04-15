from app import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import relationship, backref

class Set(db.Model):

    __tablename__ = 'set'

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50))

    tournaments = relationship('Tournament', backref='tournamentSet')

class TournamentType(db.Model):

    __tablename__ = 'tournament_type'
    
    id = db.Column(db.Integer, primary_key = True)
    description = db.Column(db.String(50))
    game_wins_required = db.Column(db.Integer)

    tournaments = relationship('Tournament', backref='tournamentType')

class Tournament(db.Model):

    __tablename__ = 'tournament'

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50))
    type = db.Column(db.Integer, db.ForeignKey('tournament_type.id'))
    set_id = db.Column(db.Integer, db.ForeignKey('set.id'))
    date = db.Column(db.Date)
    winners = db.Column(db.String(300))

    matches = relationship('Match', backref='tournament')
    statistics = relationship('Statistics', backref='tournament')

class Match(db.Model):

    __tablename__ = 'match'

    id = db.Column(db.Integer, primary_key = True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'))

    participants = relationship("MatchParticipant", backref="matches")

class Player(db.Model):

    __tablename__ = 'player'

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(30))
    name = db.Column(db.String(30))
    password = db.Column(db.String(30))
    slackUser = db.Column(db.String(21))

    def is_authenticated(self):
        return True
 
    def is_active(self):
        return True
 
    def is_anonymous(self):
        return False
 
    def get_id(self):
        return self.id

    entities = relationship("EntityParticipant", backref="player")

class Entity(db.Model):

    __tablename__ = 'entity'

    id = db.Column(db.Integer, primary_key = True)

    matches = relationship("MatchParticipant", backref="entity")
    participants = relationship("EntityParticipant", backref="entities")

class EntityParticipant(db.Model):

    __tablename__ = 'entity_participant'   

    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), primary_key = True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), primary_key = True)

class MatchParticipant(db.Model):

    __tablename__ = 'match_participant'   

    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), primary_key = True)
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), primary_key = True)
    game_wins = db.Column(db.Integer)

class Statistics(db.Model):

    __tablename__ = 'statistics'

    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), primary_key = True)
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), primary_key = True)

    position = db.Column(db.Integer)
    match_wins = db.Column(db.Integer)
    match_losses = db.Column(db.Integer)
    match_win_percentage = db.Column(db.Float)
    game_wins = db.Column(db.Integer)
    game_losses = db.Column(db.Integer)
    game_win_percentage = db.Column(db.Float)
    matches_unfinished = db.Column(db.Integer)

    entity = relationship("Entity", foreign_keys=[entity_id], backref="entity")
