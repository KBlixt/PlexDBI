# PlexDatabaseEditor

only for python3 on linux systems

a Python3 script that is intended to manipulate Plex's homescreen table "Recently added movies" it can also use the tmdb-api
if the user have an api key. otherwise that'll be ignored.
----------
whenever this script is run the Recently added movie table will be "refreshed" and from left to right
the following movies will appear:

1. The movie in the database with the latest release date.
2. The movie in the database with the 2nd latest release date.
3. The movie in the database with the 3rd latest release date.
4. The movie in the database with the 4th latest release date. Provided that it isn't more than 14 day older than the latest.
5. The movie in the database with the 5th latest release date. Provided that it isn't more than 14 day older than the latest.
6. The movie in the database with the 6th latest release date. Provided that it isn't more than 14 day older than the latest.
7. The movie in the database with the 7th latest release date. Provided that it isn't more than 14 day older than the latest.

8. A movie that's older than 10 years with a imdb score of 8 or more will be placed here. "Old but Gold"

9. With  the tmdb api a random movie with a relative low popularity on tmdb will be chosen.
   young movies and good rating increases likely hood of getting "picked". I call it "The Hidden Gem".

10. A movie selected randomly in the entire library

----------
INSTALLATION:

download the PlexDatabaseEditor.py file and put it somewhere. for example:

    cd opt && git clone https://github.com/KBlixt/PlexDatabaseEditor.git

claim ownership for the folder

    sudo chmod -R user:user PlexDatabaseEditor && cd PlexDatabaseEditor

and then add a "config" file:

    nano /opt/PlexDatabaseEditor/config

and copy this into it:

    [SETTINGS]
    TMDB_API_KEY = [your tmdb api key]
    MOVIE_LIBRARY_SECTION = [library section]

at this point you can run it if you give it sudo privileges, it will set up the syslink for you.
if you don't want to give it sudo privileges then make a symlink for the database using:

    ln -s "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db" "/opt/PlexDatabaseEditor/PlexDatabase.db"

then it's up to you if you wish to it to a crontab, personally i've got it scheduled once a day at 10:30 with sudo privileges.

    30 10 * * * cd /opt/PlexDatabaseEditor/  && sudo /usr/bin/python3 /opt/PlexDatabaseEditor/PlexDatabaseEditor.py

the good thing about running it with sudo privileges is that the plexmediaserver service is only stopped for a a second
instead of 5-20 seconds. the downside is of course that a script made by some random stranger have root access on your
hardware. but the script
isn't impossible to get though if you're only looking for bad stuff.

----------
FAIR WARNING:

this script will edit the PlexMediaServer database directly! specifically, it will change "added_at" in the
"metadata_items" table.

BACKUP YOUR DATABASES! just in case. though, so far I haven't managed to corrupted mine... yet.

----------




