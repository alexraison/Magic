from app.api import rebuildStatistics
from app.models import Tournament

for tournament in getTournaments():
	rebuildStatistics(tournament.id)