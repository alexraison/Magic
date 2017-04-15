from flask.ext.wtf import Form
from wtforms import TextField, SelectField, SelectMultipleField, validators, RadioField
from wtforms.validators import Required, Length

class AddPlayer(Form):
	username        = TextField('Username', validators = [Required(), validators.Length(min=2, max=30)])
	name            = TextField('Name', validators = [Required(), validators.Length(min=2, max=30)])
	slackUser       = TextField('slackUser', validators = [Required(), validators.Length(min=2, max=21)])
	password        = TextField('Password', validators = [Required(), validators.Length(min=6, max=30)])

class EditPlayer(Form):
	name            = TextField('Name', validators = [Required(), validators.Length(min=2, max=30)])
	slackUser       = TextField('slackUser', validators = [Required(), validators.Length(min=2, max=21)])
	
class AddTournament(Form):
	name            = TextField('Name', validators = [Required(), validators.Length(min=2, max=50)])
	set 			= SelectField('Set', validators = [Required()])
	players         = SelectMultipleField('Players')		

class AddTwoHeadedGiantTournament(Form):
	name            = TextField('Name', validators = [Required(), validators.Length(min=2, max=50)])
	set 			= SelectField('Set', validators = [Required()])
	pairs           = SelectMultipleField('Pairs')	

class EditTournament(Form):
	name            = TextField('Name', validators = [Required(), validators.Length(min=2, max=50)])
	set 			= SelectField('Set', validators = [Required()])

class AddSet(Form):
	name            = TextField('Name', validators = [Required(), validators.Length(min=2, max=50)])

class EditSet(Form):
	name            = TextField('Name', validators = [Required(), validators.Length(min=2, max=50)])

class AddPair(Form):
	players         = SelectMultipleField('Players')

class Pairings(Form):
	players         = SelectMultipleField('Players')

