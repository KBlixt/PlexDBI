import sqlite3
from datetime import datetime
from datetime import timedelta
import json
import urllib.request
import urllib.error
import configparser
import inspect
import sys
import time
import os


class PlexDBI:

    def __init__(self):

        start = time.time()
        try:
            self.sudo = 0 == os.getuid()
        except AttributeError as e:
            print(e.args)
            self.sudo = False

        if self.sudo:
            if not os.path.isfile('PlexDatabase.db'):
                os.system('ln -s "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/'
                          'Plug-in Support/Databases/com.plexapp.plugins.library.db" "'
                          + os.getcwd() + '/PlexDatabase.db"')

        self.db = sqlite3.connect('PlexDatabase.db')  # remember to change this back and remove API-key
        self.cursor = self.db.cursor()

        if not os.path.isfile('config'):
            f = open("config", "w+")
            if self.sudo:
                os.system("sudo chown --reference=" + os.getcwd() + "/PlexDBI.py config")
                os.system("sudo chmod 777 config")
            f.write('\n[SETTINGS]')
            f.write('\nTMDB_API_KEY = ')
            f.write('\nMOVIE_LIBRARY_SECTION =')
            f.close()

        config = configparser.ConfigParser()
        config.read('config')
        self.key = config.get('SETTINGS', 'TMDB_API_KEY')
        self.library_section = config.get('SETTINGS', 'MOVIE_LIBRARY_SECTION')
        self.check_library_section()

        movie_list = PlexDBI.recent_releases(self)
        movie_list = movie_list + PlexDBI.old_but_gold(self)
        if self.key != '':
            movie_list = movie_list + PlexDBI.hidden_gem(self)
        else:
            print("INFO: You have not specified a tmdb api key.")
        movie_list = movie_list + PlexDBI.random(self)
        PlexDBI.commit(self, movie_list)

        end = time.time()
        self.db.close()
        print("script completed in " + str(int(end - start)) + " seconds.")
        print("---End of script---")

    def check_library_section(self):
        library_is_good = False
        for library in self.cursor.execute("SELECT id "
                                           "FROM library_sections "
                                           "WHERE language IS NOT 'xn' "
                                           "AND section_type = 1 "
                                           "ORDER BY id ASC "):
            if str(library[0]) == self.library_section:
                library_is_good = True

        if not library_is_good:
            print('Your MOVIE_LIBRARY_SECTION parameter in the config file is not a Movie library.')
            print('These libraries are movie libraries and can be used in this script:')
            print('--------------------------------------------------------------------------')

            for library in self.cursor.execute("SELECT id, name "
                                               "FROM library_sections "
                                               "WHERE language IS NOT 'xn' "
                                               "AND section_type = 1 "
                                               "ORDER BY id ASC "):

                print('The library "' + library[1] + '" have section_id: ' + str(library[0]) + '.')
                sys.exit()

    def get_reference_date(self, attempts_limit=5):
        try:
            self.cursor.execute("SELECT originally_available_at "  # most recent movie for reference
                                "FROM metadata_items "
                                "WHERE library_section_id = ? "
                                "AND metadata_type = 1 "
                                "AND duration > 1 "
                                "ORDER BY originally_available_at DESC "
                                "LIMIT ?", (self.library_section, attempts_limit,))
        except Exception:
            print('Remember to fill in the MOVIE_LIBRARY_SECTION in the config file. ')
            print('Also make sure that the "PlexDatabase.db" syslink isn\'t broken. ')
            print('here is a list on viable libraries you have: ')
            print('----------------------------------------------------------------')
            print('Exiting')

            sys.exit()
        reference_date = ''
        attempt_number = 0
        for attempt in self.cursor.fetchall():
            reference_date = attempt[0]
            attempt_number += 1

            if reference_date != 'None':
                break
            if attempt_number == attempts_limit:
                print("---script failed---")
                print("Failed finding a reference date. exiting on line: "
                      + (self.line_number() + 2) + ".")
                sys.exit()

        reference_date = datetime.strptime(reference_date, '%Y-%m-%d %H:%M:%S') + timedelta(days=-14)

        return reference_date

    def recent_releases(self, recent_releases_minimum=3, recent_releases_limit=7):
        reference_date = PlexDBI.get_reference_date(self)
        local_movie_list = list()
        if recent_releases_limit > 0:
            for movieInfo in self.cursor.execute("SELECT id,title "  # modifies 7 movies within 14 days...
                                                 "FROM metadata_items "
                                                 "WHERE library_section_id = ? "
                                                 "AND duration > 1 "
                                                 "AND originally_available_at > ? "
                                                 "ORDER BY originally_available_at DESC "
                                                 "LIMIT ?", (self.library_section,
                                                             reference_date.isoformat().replace('T', ' '),
                                                             recent_releases_limit)):

                movie_id = movieInfo[0]
                title = str(movieInfo[1])

                if title == 'None':
                    print("---script failed---")
                    print("No title were found for a movie and it was skipped.")
                    print("Not a critical error and can be ignored unless it's a common occurrence.")
                    print("movie_id: " + movie_id)
                    continue
                if movie_id == 'None':
                    print("---script failed---")
                    print("No id were found for a movie and it was skipped.")
                    print("Not a critical error and can be ignored unless it's a common occurrence.")
                    continue

                local_movie_list.append(movie_id)
                print('Movie with id: ' + str(movie_id) + ' was added to the queue')

        if recent_releases_minimum-len(local_movie_list) > 0:
            for movieInfo in self.cursor.execute("SELECT id,title "  # ...but at least the last 3 movies
                                                 "FROM metadata_items "
                                                 "WHERE library_section_id = ? "
                                                 "AND duration > 1 "
                                                 "AND originally_available_at < ? "
                                                 "ORDER BY originally_available_at DESC "
                                                 "LIMIT ?", (self.library_section,
                                                             reference_date.isoformat().replace('T', ' '),
                                                             recent_releases_minimum - len(local_movie_list),)):

                movie_id = movieInfo[0]
                title = str(movieInfo[1])

                if title == 'None':
                    print("---script failed---")
                    print("No title were found for a movie and it was skipped.")
                    print("Not a critical error and can be ignored unless it's a common occurrence.")
                    print("movie_id: " + movie_id)
                    continue
                if movie_id == 'None':
                    print("---script failed---")
                    print("No id were found for a movie and it was skipped.")
                    print("Not a critical error and can be ignored unless it's a common occurrence.")
                    continue

                local_movie_list.append(movie_id)
                print('Movie with id: ' + str(movie_id) + ' was added to the queue')

        return local_movie_list

    def old_but_gold(self, count=1):
        local_movie_list = list()
        for movie_info in self.cursor.execute("SELECT id,title "  # old but gold
                                              "FROM metadata_items "
                                              "WHERE id IN (SELECT id FROM metadata_items ORDER BY RANDOM()) "
                                              "AND originally_available_at < ? "
                                              "AND rating > 8 "
                                              "AND library_section_id = ? "
                                              "ORDER BY RANDOM() "
                                              "LIMIT ?", (datetime.now() + timedelta(days=+3652),
                                                          self.library_section, count,)):

            movie_id = movie_info[0]
            title = str(movie_info[1])

            if title == 'None':
                print("---script failed---")
                print("No title were found for a movie and it was skipped.")
                print("Not a critical error and can be ignored unless it's a common occurrence.")
                print("movieId: " + movie_id)
                continue
            if movie_id == 'None':
                print("---script failed---")
                print("No id were found for a movie and it was skipped.")
                print("Not a critical error and can be ignored unless it's a common occurrence.")
                continue

            local_movie_list.append(movie_id)
            print('Movie with id: ' + str(movie_id) + ' was added to the queue')

        return local_movie_list

    def hidden_gem(self, count=1):
        local_movie_list = list()

        lowest_popularity = 100000.0
        selected_id = -1
        for i in range(count):

            for movie_info in self.cursor.execute("SELECT id,title,year,rating "  # Potential hidden gem
                                                  "FROM metadata_items "
                                                  "WHERE id IN (SELECT id FROM metadata_items ORDER BY RANDOM()) "
                                                  "AND library_section_id = ? "
                                                  "AND rating > 1 "
                                                  "ORDER BY RANDOM() "
                                                  "LIMIT 8", (self.library_section, )):
                movie_id = movie_info[0]
                title = str(movie_info[1])
                year = str(movie_info[2])
                rating = movie_info[3]

                if title == 'None':
                    print("---script failed---")
                    print("No title were found for a movie and it was skipped.")
                    print("Not a critical error and can be ignored unless it's a common occurrence.")
                    print("movie_id: " + movie_id)
                    print("year: " + year)
                    print("rating: " + rating)
                    continue
                if movie_id == 'None':
                    print("---script failed---")
                    print("No id were found for the movie \"" + title + "\" and it was skipped.")
                    print("Not a critical error and can be ignored unless it's a common occurrence.")
                    continue
                if year == 'None':
                    print("---script failed---")
                    print("No year were found for the movie \"" + title + "\" and it was skipped.")
                    print("Not a critical error and can be ignored unless it's a common occurrence.")
                    continue
                if rating == 'None':
                    print("---script failed---")
                    print("No rating were found for the \"" + title + "\" and it was skipped.")
                    print("Not a critical error and can be ignored unless it's a common occurrence.")
                    continue

                title = title.replace(' ', '+')
                title = title.encode('ascii', errors='ignore')  # sanitise title from unicode characters
                title = title.decode('utf-8')

                try:

                    response = urllib.request.urlopen('https://api.themoviedb.org/3/search/movie'
                                                      '?api_key=' + self.key +
                                                      '&query=' + title +
                                                      '&year=' + year)
                    data = json.loads(response.read().decode('utf-8'))

                except urllib.error.HTTPError as e:
                    print("---script failed---")
                    print("TMDB api failed, skipping one movie from the category 'Hidden Gems' see error: ")
                    print("URL requested: " + e.geturl())
                    print("Reason: " + e.reason)
                    continue

                if data['total_results'] > 0:
                    compensated_pop = float(data['results'][0]['popularity']) * \
                                      (1.05 ** (2015 - int(year))) * \
                                      (1/(rating**1.2))
                    if lowest_popularity > compensated_pop:
                        lowest_popularity = compensated_pop
                        selected_id = movie_id

            if selected_id >= 0:
                local_movie_list.append(selected_id)
                print('Movie with id: ' + str(selected_id) + ' was added to the queue')

        return local_movie_list

    def random(self, count=1):
        local_movie_list = list()

        for row in self.cursor.execute("SELECT id,title  "  # Random
                                       "FROM metadata_items "
                                       "WHERE id IN (SELECT id FROM metadata_items ORDER BY RANDOM()) "
                                       "AND library_section_id = ? "
                                       "ORDER BY RANDOM() "
                                       "LIMIT ?", (self.library_section, count,)):

            movie_id = row[0]
            title = str(row[1])

            if title == 'None':
                print("---script failed---")
                print("No title were found for a movie and it was skipped.")
                print("Not a critical error and can be ignored unless it's a common occurrence.")
                print("movie_id: " + movie_id)
                continue
            if movie_id == 'None':
                print("---script failed---")
                print("No id were found for the movie \"" + title + "\" and it was skipped.")
                print("Not a critical error and can be ignored unless it's a common occurrence.")
                continue

            local_movie_list.append(movie_id)
            print('Movie with id: ' + str(movie_id) + ' was added to the queue')

        return local_movie_list

    def commit(self, id_list):
        if self.sudo:
            print('Stopping plexmediaserver:...')
            os.system("sudo service plexmediaserver stop.")

        pos = 0
        print('Processing movie list...')
        timestamp = datetime.now().replace(microsecond=0) + timedelta(days=+1)
        for movie in id_list:
            now = timestamp + timedelta(seconds=-pos)
            self.cursor.execute("UPDATE metadata_items "
                                "SET added_at = ?"
                                "WHERE id = ?", (now.isoformat().replace('T', ' '), movie,))
            pos += 1
        print('Movie list processed, committing to db.')
        self.db.commit()
        print('changes comitted.')
        if self.sudo:
            print('Starting plexmediaserver...')
            os.system("sudo service plexmediaserver start.")
        else:
            print('you can now proceed to restart your plex server')

    @staticmethod
    def line_number():
        return inspect.currentframe().f_back.f_lineno


plex = PlexDBI()
