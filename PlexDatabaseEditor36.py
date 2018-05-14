# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime
from datetime import timedelta
import json
import urllib.request
import configparser
import string

config = configparser.ConfigParser()
config.read('PlexDatabaseEditor.config')

print(config.get('TMDB', 'API_KEY'))
response = urllib.request.urlopen('http://www.python.org/')
key = config.get('TMDB', 'API_KEY')

# db = sqlite3.connect('PlexDatabase.db')               # remember to change this back and remove API-key
db = sqlite3.connect('testingDatabase.db')

cursor = db.cursor()
cursor2 = db.cursor()
pos = 0
RecentReleasesMinimum = 3
RecentReleasesLimit = 7
timestamp = datetime.now().replace(microsecond=0) + timedelta(days=+1)
referenceDate = ''

cursor.execute("SELECT id,title,originally_available_at,rating_count "  # most recent movie for reference
                      "FROM metadata_items "
                      "WHERE library_section_id = 1 "
                      "AND metadata_type = 1 "
                      "AND duration > 1 "
                      "ORDER BY originally_available_at DESC "
                      "LIMIT 1")
rresponse = cursor.fetchone()
referenceDate = datetime.strptime(rresponse[2], '%Y-%m-%d %H:%M:%S') + timedelta(days=-14)

########################################################################################################################

if RecentReleasesLimit > 0:
    for row in cursor.execute("SELECT id,title,originally_available_at "  # 7 movies within 14 days...
                              "FROM metadata_items "
                              "WHERE library_section_id = 1 "
                              "AND metadata_type = 1 "
                              "AND duration > 1 "
                              "AND originally_available_at > ? "
                              "ORDER BY originally_available_at DESC "
                              "LIMIT ? ", (referenceDate.isoformat().replace('T', ' '), RecentReleasesLimit)):

        now = timestamp + timedelta(seconds=10-pos)

        cursor2.execute("UPDATE metadata_items "
                        "SET added_at = ?"
                        "WHERE id = ?", (now.isoformat().replace('T', ' '), row[0],))

        pos = pos + 1
db.commit()
########################################################################################################################

if RecentReleasesMinimum-pos > 0:
    for row in cursor.execute("SELECT id,title,originally_available_at "  # ...but at least the last 3 movies
                              "FROM metadata_items "
                              "WHERE library_section_id = 1 "
                              "AND metadata_type = 1 "
                              "AND duration > 1 "
                              "AND originally_available_at < ? "
                              "ORDER BY originally_available_at DESC "
                              "LIMIT ?", (referenceDate.isoformat().replace('T', ' '), RecentReleasesMinimum - pos,)):

        now = timestamp + timedelta(seconds=10-pos)

        cursor2.execute("UPDATE metadata_items "
                        "SET added_at = ?"
                        "WHERE id = ?", (now.isoformat().replace('T', ' '), row[0],))

        pos = pos + 1

db.commit()
########################################################################################################################

for row in cursor.execute("SELECT id,title "  # old but gold
                          "FROM metadata_items "
                          "WHERE id IN (SELECT id FROM metadata_items ORDER BY RANDOM()) "
                          "AND originally_available_at < '2007-01-01 00:00:00' "
                          "AND rating > 8 "
                          "AND library_section_id = 1 "
                          "AND metadata_type = 1 "
                          "ORDER BY RANDOM() "
                          "LIMIT 1"):

    now = timestamp + timedelta(seconds=10-pos)

    cursor2.execute("UPDATE metadata_items "
                    "SET added_at = ?"
                    "WHERE id = ?", (now.isoformat().replace('T', ' '), row[0],))

    pos = pos + 1
db.commit()
########################################################################################################################
maxPopularity = 100000.0
selection = 20
for row in cursor.execute("SELECT id,title,year,rating "  # Potential hidden gem
                          "FROM metadata_items "
                          "WHERE id IN (SELECT id FROM metadata_items ORDER BY RANDOM()) "
                          "AND library_section_id = 1 "
                          "AND metadata_type = 1 "
                          "AND rating > 1 "
                          "ORDER BY RANDOM() "
                          "LIMIT 7"):

    title = str(row[1].replace(' ', '+'))
    year = str(row[2])
    rating = row[3]

    title = title.encode('ascii', errors='ignore')
    title = title.decode('utf-8')



    response = urllib.request.urlopen('https://api.themoviedb.org/3/search/movie'
                                      '?api_key=' + key +
                                      '&query=' + title +
                                      '&year=' + year)

    data = json.loads(response.read().decode('utf-8'))

    if data['total_results'] > 0:

        print(title, + float(data['results'][0]['popularity']) * (1.05 ** (2015 - int(year))) * (1/(rating**1.5)))
        if maxPopularity > float(data['results'][0]['popularity']) * (1.05 ** (2015 - int(year))) * (1/(rating**1.5)):
            maxPopularity = float(data['results'][0]['popularity']) * (1.05 ** (2015 - int(year))) * (1/(rating**1.5))
            selection = row[0]
            print('--')


if selection >= 0:

    now = timestamp + timedelta(seconds=10 - pos)

    cursor2.execute("UPDATE metadata_items "
                    "SET added_at = ?"
                    "WHERE id = ?", (now.isoformat().replace('T', ' '), selection,))

    pos = pos + 1
    db.commit()
########################################################################################################################

for row in cursor.execute("SELECT id,title "  # Random
                          "FROM metadata_items "
                          "WHERE id IN (SELECT id FROM metadata_items ORDER BY RANDOM()) "
                          "AND library_section_id = 1 "
                          "AND metadata_type = 1 "
                          "ORDER BY RANDOM() "
                          "LIMIT 1"):

    now = timestamp + timedelta(seconds=10-pos)

    cursor2.execute("UPDATE metadata_items "
                    "SET added_at = ?"
                    "WHERE id = ?", (now.isoformat().replace('T', ' '), row[0],))

    pos = pos + 1
db.commit()
########################################################################################################################

db.close()
