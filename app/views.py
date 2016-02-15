from flask import render_template, url_for, request, flash, redirect, Flask, session, g
from flask.ext.login import LoginManager, login_user , logout_user , current_user
from sqlalchemy import func

from app import app
from app.forms import *
from app.api import *

#############################################
# Authentication
#############################################   
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
	return Player.query.get(int(id))
    
def is_public(function):
    function.is_public = True
    return function

@app.route('/login',methods=['GET','POST'])
@is_public
def login():

	if request.method == 'GET':
		return render_template('login.html', pageName = 'Login')

	username = request.form['username']
	password = request.form['password']

	registered_user = Player.query.filter_by(func.upper(username)=username.upper(),password=password).first()

	if registered_user is None:
		flash('Username or Password is invalid' , 'error')
		return redirect(url_for('login'))

	login_user(registered_user, remember=True)

	return redirect(url_for('viewOutstandingMatches'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login')) 

@app.before_request
def before_request():
	g.user = current_user
	if not g.user.is_authenticated and not getattr(app.view_functions[request.endpoint], 'is_public', False) and request.endpoint != 'static':
			return redirect(url_for('login'))

#############################################
# Routing
#############################################
@app.route('/', methods = ['GET', 'POST'])
def viewOutstandingMatches():

	if request.method == 'POST':
		entityResults = [{'entityId':int(request.form['player_one_id']), 'gameWins':int(str(request.form['score'])[0:1])}, {'entityId':int(request.form['player_two_id']), 'gameWins':int(str(request.form['score'])[1:2])}]
		updateMatchResult(request.form['match_id'], entityResults)	

	return render_template("home.html", matches = getOutstandingMatches(), pageName = 'Matches left to play', currentPlayer = getCurrentPlayer(g.user.username), players=getPlayers())

@app.route('/results', methods = ['GET'])
def viewUnfinishedTournamentResults():

	return render_template("results.html", tournaments=getUnfinishedTournamentResults(id))

@app.route('/lifetimestatistics', methods = ['GET'])
def viewStatistics():

	return render_template("lifetime_statistics.html", lifetimeStatistics=getLifetimeStatistics(), pageName = 'Lifetime Statistics')

@app.route('/yearbyyearstatistics', methods = ['GET'])
def viewYearByYearStatistics():

	return render_template("year_by_year_statistics.html", yearByYearStats=getyearByYearStatistics(), pageName = 'Year By Year Statistics')

@app.route('/byset', methods = ['GET'])
def viewStatisticsBySet():

	return render_template("statistics_by_set.html", statisticsBySet=getStatisticsBySet(), pageName = 'Statistics By Set')

@app.route('/head-to-head', methods = ['GET'])
def viewHeadToHead():

	return render_template("head_to_head.html", currentPlayer = getCurrentPlayer(g.user.username), players=getPlayers(), playerHeadToHeadData = getPlayerHeadToHeadData(), pageName = 'Head to Head Statistics')

#############################################
# Player Routes
############################################# 	
@app.route('/player', methods = ['GET'])
def viewPlayers():

    return render_template("players.html", players=getPlayers(), pageName = 'Players')

@app.route('/player/add', methods = ['GET','POST'])
def addPlayer():

	form = AddPlayer()

	if form.validate_on_submit():
	
		if usernameAlreadyTaken(form.username.data):
			flash('Username already taken')
		else:	
			createPlayer(form.name.data, form.email.data, form.password.data, form.username.data)
			return redirect(url_for('viewPlayers'))

	return render_template("form.html", form=form, pageName = 'Add Player')

@app.route('/player/edit/<int:id>', methods = ['GET', 'POST'])
def editPlayer(id):

	player = getPlayer(id)
	form = EditPlayer(name=player.name, email=player.email)
		
	if form.validate_on_submit():
		updatePlayer(id, form.name.data, form.email.data)
		return redirect(url_for('viewPlayers'))
			
	return render_template("form.html", form=form, pageName = 'Edit Player')

@app.route('/pair/add', methods = ['GET','POST'])
def addPair():

	form = AddPair()
	form.players.choices = [(str(g.id), g.name) for g in Player.query.order_by('name')]

	if form.validate_on_submit():
	
		if len(form.players.data) != 2:
			flash('Exactly two players must be selected')
		elif pairAlreadyExists(form.players.data):
			flash('Pair already exists')			
		else:
			createPair(form.players.data)
			flash('Pair created')	
			return redirect(url_for('addPair'))

	return render_template("form.html", form=form, pageName = 'Add Pair')

#############################################
# Set Routes
############################################# 	
@app.route('/set', methods = ['GET'])
def viewSets():
	
	return render_template("sets.html", sets=getSets(), pageName = 'Sets')

@app.route('/set/add', methods = ['GET', 'POST'])
def addSet():

	form = AddSet()

	if form.validate_on_submit():
		createSet(form.name.data)
		return redirect(url_for('viewSets'))
		
	return render_template("form.html", form=form, pageName = 'Add Set')

@app.route('/set/edit/<int:id>', methods = ['GET', 'POST'])
def editSet(id):

	set = getSet(id)
	form = EditSet(name = set.name)
		
	if form.validate_on_submit():
		updateSet(id, form.name.data)
		return redirect(url_for('viewSets'))
			
	return render_template("form.html", form=form, pageName = 'Edit Set')

#############################################
# Tournament Routes
############################################# 
@app.route('/tournament', methods = ['GET'])
def viewTournaments():

	return render_template("tournaments.html", tournaments=getTournaments(), pageName = 'Tournaments')

@app.route('/tournament/add', methods = ['GET', 'POST'])
def addTournament():

	form = AddTournament()

	subQuery = db.session.query(EntityParticipant.entity_id).group_by(EntityParticipant.entity_id).having(func.count(EntityParticipant.entity_id) == 1).subquery()
	form.players.choices = [(str(g.id), g.participants[0].player.name) for g in Entity.query.filter(Entity.id.in_(subQuery)).all()]

	form.set.choices = [(str(g.id), g.name) for g in Set.query.order_by('id')]

	if form.validate_on_submit():
	
		if len(form.players.data) < 2:
			flash('At least two players must be selected')
		else:
			createTournament(form.name.data, form.set.data, form.players.data, 'NORMAL')
			return redirect(url_for('viewTournaments'))
		
	return render_template("form.html", form=form, pageName = 'Add Tournament')
	
@app.route('/tournament/addtwoheadedgiant', methods = ['GET', 'POST'])
def addTwoHeadedGiantTournament():

	form = AddTwoHeadedGiantTournament()

	subQuery = db.session.query(EntityParticipant.entity_id).group_by(EntityParticipant.entity_id).having(func.count(EntityParticipant.entity_id) == 2).subquery()
	form.pairs.choices = [(str(g.id), g.participants[0].player.name + ' - ' + g.participants[1].player.name) for g in Entity.query.filter(Entity.id.in_(subQuery)).all()]
	form.set.choices = [(str(g.id), g.name) for g in Set.query.order_by('id')]

	if form.validate_on_submit():
	
		if len(form.pairs.data) < 2:
			flash('At least two pairs must be selected')
		else:
			createTournament(form.name.data, form.set.data, form.pairs.data, 'TWOHEADEDGIANT')
			return redirect(url_for('viewTournaments'))
		
	return render_template("form.html", form=form, pageName = 'Add Two Headed Giant Tournament')

@app.route('/tournament/edit/<int:id>', methods = ['GET', 'POST'])
def editTournament(id):

	tournament = getTournament(id)

	set = tournament.tournamentSet.id if tournament.tournamentSet else ''

	form = EditTournament(name = tournament.name, set = set)
	form.set.choices = [('', '')]
	form.set.choices += [(str(g.id), g.name) for g in Set.query.order_by('id')]

	if form.validate_on_submit():
		updateTournament(id, form.name.data, form.set.data)
		return redirect(url_for('viewTournaments'))
			
	return render_template("form.html", form=form, pageName = 'Edit Tournament')

@app.route('/tournament/matches/<int:id>', methods = ['GET', 'POST'])
def viewTournamentMatches(id):

	if request.method == 'POST':
		entityResults = [{'entityId':int(request.form['player_one_id']), 'gameWins':int(str(request.form['score'])[0:1])}, {'entityId':int(request.form['player_two_id']), 'gameWins':int(str(request.form['score'])[1:2])}]
		updateMatchResult(request.form['match_id'], entityResults)	

	return render_template("home.html", matches = getTournamentMatches(id), pageName = getTournamentName(id) + ' - Matches', currentPlayer = None, players=getPlayers())

@app.route('/tournament/results/<int:id>', methods = ['GET'])
def viewTournamentResults(id):

	return render_template("results.html", tournaments=[getTournamentResults(id)])

#############################################
# Start Application
############################################# 
if __name__ == "__main__":
	app.run()
