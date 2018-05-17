# PlexDBI
This Python3 script is intended to manipulate Plex's homescreen table "Recently added movies" it can also use the tmdb-api
if the user have an api key. Otherwise that'll be ignored.

Whenever this script is run, the Recently added movie table will be "refreshed" and from left to right
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

**This can now be modified to your liking in the config file.**

----------
### linux INSTALLATION:

download the PlexDBI.py file and put it somewhere. for example:
```sh
    cd /opt && git clone https://github.com/KBlixt/PlexDBI.git && cd PlexDBI
```
At this point you can run it. If you give it sudo privileges, it will set up the syslink for the database and the config file for you.
but you'll still have to configure the config file. But just run the script and it will tell you what's wrong
and how to fix it.
```sh
    sudo python3 PlexDBI.py
```
Then it's up to you if you wish to add it to a crontab schedule, personally i've got it scheduled once a day at 10:30
with sudo privileges.
```sh
    30 10 * * * cd /opt/PlexDBI/  && sudo /usr/bin/python3 /opt/PlexDBI/PlexDBI.py
```
If you don't want to give it sudo privileges then you'll have make a symlink for the database. i.e:
```sh
    ln -s "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db" PlexDatabase.db
```
Without sudo privilege you'll have to remember to stop plexmediaserver before you run the script and then restart it
since it can't shut down the plex service without sudo privileges. Now, I've been running this script plenty of times
with plex still online so I think it's ok, but I'm not sure. better safe than sorry. Although, if you run it while
plex is online it will act a bit funky until you restart the plex service.

----------
### Other INSTALLATIONS

#### for windows and mac:
As long as you guys haven't changed the default installation paths to the plex media server app
you really just need to download the python script and run it  with python3, however you guys do that.
preferably run it in a command window, then it'll instruct you of what's wrong and how to fix it. Otherwise make sure
the config file is filled out correctly.

#### for NAS and other OS:
I really have no clue. if you setup the config file and the database link manually then the
script should run as long as you can run python3 code.

----------
## FAIR WARNING:

This script will edit the PlexMediaServer database directly! Specifically, it will change "added_at" in the
"metadata_items" table.

Backup your database! Just in case really but so far I haven't managed to corrupted mine. And I've been pretty rough.

----------
