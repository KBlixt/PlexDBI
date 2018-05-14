# PlexDatabaseEditor

a small script that is intended to manipulate Plex's homescreen table "Recently added movies" it can also use tmdb api
if the user have an api key. otherwise that'll be ignored.
----------
whenever this script is run the Recently added movie table will be "refreshed" and from right to left
the following movies will appear:

1. The movie in the database with the latest release date.
2. The movie in the database with the 2nd latest release date.
3. The movie in the database with the 3rd latest release date.
4. The movie in the database with the 4th latest release date. Provided that it isn't more than 14 day older than 1.
5. The movie in the database with the 5th latest release date. Provided that it isn't more than 14 day older than 1.
6. The movie in the database with the 6th latest release date. Provided that it isn't more than 14 day older than 1.
7. The movie in the database with the 7th latest release date. Provided that it isn't more than 14 day older than 1.

8. A movie that's older than 10 years with a imdb score of 8 or more will be placed here. "Old but Gold"

9. With  the tmdb api a random movie with a relative low popularity on tmdb will be chosen.
   young movies and good rating increases likely hood of getting "picked". I call it "The Hidden Gem".
   Without the api a movie will be selected randomly in the entire library

10. A movie selected randomly in the entire library

----------
INSTALLATION:

don't... for now.

----------

this script will edit the PlexMediaServer database directly! specifically it will change "added_at" in the
"metadata_items" table.
----------
NOTES!!

    very early stage script. currently these caveats and limitations exists:

    -  library section id must be "1"
    -  library craches if a movie name contain any character that python can't deal with.
    -  if you don't have a api key it will crash (setting up ignore on these segments is on the do-list
    -  the database must be symlinked into the folder
    -  plex should, preferably, not be online while this script is running and then restarted when it's finished.
    -  i think that installing sqlite3 is a requirement, but i'm unsure
    -  I've only run this on python 2.7.12 in ubuntu 16.04 any other OS and python versions is unknown if they work.
    -  a script that is calling this script should be setup and a cronjob should be added for maximum effect
    -  other.. things.. ??? no clue what might go wrong.
    -  BACKUP YOUR DATABASES! just in case. though, so far I haven't managed to corrupted mine... yet.
    -  testing the script is recommended to do on a testing db by copying the plex db and call it "testingDatabase.db"



