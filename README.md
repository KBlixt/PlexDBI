# PlexDatabaseEditor

a small script that is intended to manipulate Plex's homescreen table "Recently added movies" it can also use the tmdb-api
if the user have an api key. otherwise that'll be ignored.
----------
whenever this script is run the Recently added movie table will be "refreshed" and from left to right
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

10. A movie selected randomly in the entire library

----------
INSTALLATION:

download the PlexDatabaseEditor.py file, put it somewhere. 
add a "PlexDatabaseEditor.config" file

with the following information in it:

    [SETTINGS]
    TMDB_API_KEY = d2347c5b228e909370baa85a74702611
    MOVIE_LIBRARY_SECTION = 1

and run the script with sudo priveliges. it needs sudo priveligies to stop and start the plexmediaserver service. 
if you feel uncumfortable with this then remove those lines of code in the script, just delete any line with the word 
"plexmediaserver" in it. then make sure that you have the plex database in the folder named "PlexDatabase.db" 
otherwise it will crash. no harm will be done but it won't work.

I'll probably fix so that it won't require sudo to run propperly some day.

----------

this script will edit the PlexMediaServer database directly! specifically, it will change "added_at" in the
"metadata_items" table.

  BACKUP YOUR DATABASES! just in case. though, so far I haven't managed to corrupted mine... yet. and I'm runnign this script every 10 minute just to see what will happen, I even axcidentally ran twice at the same time and as far as I'm aware nothing happend.
----------
NOTES!!

    very early stage script. currently these caveats and limitations exists:

    -  if you don't have a api key it will crash (setting up ignore on these segments is on the do-list
    -  a script that is calling this script should be setup and a cronjob should be added for maximum effect
    -  BACKUP YOUR DATABASES! just in case. though, so far I haven't managed to corrupted mine... yet.
    -  the database must be symlinked into the folder



