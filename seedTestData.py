import psycopg2
from app.api import *
import os
import urllib.parse as urlparse

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

pgCursor.execute('INSERT INTO player (username, password, name, email) VALUES(%s, %s, %s, %s)', ['test', 'password', 'Test Name', 'email@email.com'])
pgConn.commit()