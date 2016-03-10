from app.api import *
from app.models import Tournament

for tournament in getTournaments():
	rebuildStatistics(tournament.id)
	print(tournament.id)
print("end")