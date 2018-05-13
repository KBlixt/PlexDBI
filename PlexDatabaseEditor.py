import sqlite3
from datetime import datetime
from datetime import timedelta


db = sqlite3.connect('test.db')
cursor = db.cursor()
cursor2 = db.cursor()
pos = 0
RecentReleasesMinimum = 3
RecentReleasesLimit = 7
timestamp = datetime.now().replace(microsecond=0)


for row in cursor.execute("SELECT id,title,originally_available_at "  # senaste filmen
                          "FROM metadata_items "
                          "WHERE library_section_id = 1 "
                          "AND duration > 1 "
                          "ORDER BY originally_available_at DESC "
                          "LIMIT 1"):

    referenceDate = row[2]
    date = datetime.strptime(referenceDate, '%Y-%m-%d %H:%M:%S')
    date = date + timedelta(days=-14)

########################################################################################################################

if RecentReleasesLimit > 0:
    for row in cursor.execute("SELECT id,title,originally_available_at "  # 7 movies within 14 days
                              "FROM metadata_items "
                              "WHERE library_section_id = 1 "
                              "AND duration > 1 "
                              "AND originally_available_at > ? "
                              "ORDER BY originally_available_at DESC "
                              "LIMIT ? ", (date.isoformat().replace('T', ' '), RecentReleasesLimit)):

        now = timestamp + timedelta(seconds=10-pos)

        cursor2.execute("UPDATE metadata_items "
                        "SET added_at = ?"
                        "WHERE id = ?", (now.isoformat().replace('T', ' '), row[0],))


        pos = pos + 1
db.commit()
########################################################################################################################

if RecentReleasesMinimum-pos > 0:
    for row in cursor.execute("SELECT id,title,originally_available_at "  # at least the last 3 movies
                              "FROM metadata_items "
                              "WHERE library_section_id = 1 "
                              "AND duration > 1 "
                              "AND originally_available_at < ? "
                              "ORDER BY originally_available_at DESC "
                              "LIMIT ?", (date.isoformat().replace('T', ' '), RecentReleasesMinimum - pos,)):

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
                          "ORDER BY RANDOM() "
                          "LIMIT 1"):

    now = timestamp + timedelta(seconds=10-pos)

    cursor2.execute("UPDATE metadata_items "
                   "SET added_at = ?"
                   "WHERE id = ?", (now.isoformat().replace('T', ' '), row[0],))


    pos = pos + 1
db.commit()
########################################################################################################################

for row in cursor.execute("SELECT id,title "  # random no.1
                          "FROM metadata_items "
                          "WHERE id IN (SELECT id FROM metadata_items ORDER BY RANDOM()) "
                          "AND library_section_id = 1 "
                          "ORDER BY RANDOM() "
                          "LIMIT 1"):

    now = timestamp + timedelta(seconds=10-pos)

    cursor2.execute("UPDATE metadata_items "
                   "SET added_at = ?"
                   "WHERE id = ?", (now.isoformat().replace('T', ' '), row[0],))


    pos = pos + 1
db.commit()
########################################################################################################################

for row in cursor.execute("SELECT id,title "  # random no.2
                          "FROM metadata_items "
                          "WHERE id IN (SELECT id FROM metadata_items ORDER BY RANDOM()) "
                          "AND library_section_id = 1 "
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