# -*- coding: utf-8 -*-
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


class PlexDatabaseEditor:

    def __init__(self):
        start = time.time()

        config = configparser.ConfigParser()
        config.read('PlexDatabaseEditor.config')

        self.db = sqlite3.connect('PlexDatabase.db')  # remember to change this back and remove API-key
        self.cursor = self.db.cursor()

        self.key = config.get('TMDB', 'API_KEY')

        movie_list = PlexDatabaseEditor.recent_releases(self)
        movie_list = movie_list + PlexDatabaseEditor.old_but_gold(self)
        movie_list = movie_list + PlexDatabaseEditor.hidden_gem(self)
        movie_list = movie_list + PlexDatabaseEditor.random(self)
        PlexDatabaseEditor.commit(self, movie_list)

        end = time.time()
        self.db.close()
        print("script completed in " + str(int(end - start)) + " seconds.")
        print("---script was completed---")

    def get_reference_date(self, attempts_limit=5):
        self.cursor.execute("SELECT originally_available_at "  # most recent movie for reference
                            "FROM metadata_items "
                            "WHERE library_section_id = 1 "
                            "AND metadata_type = 1 "
                            "AND duration > 1 "
                            "ORDER BY originally_available_at DESC "
                            "LIMIT ?", (attempts_limit,))

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
        reference_date = PlexDatabaseEditor.get_reference_date(self)
        local_movie_list = list()
        if recent_releases_limit > 0:
            for movieInfo in self.cursor.execute("SELECT id,title "  # modifies 7 movies within 14 days...
                                                 "FROM metadata_items "
                                                 "WHERE library_section_id = 1 "
                                                 "AND metadata_type = 1 "
                                                 "AND duration > 1 "
                                                 "AND originally_available_at > ? "
                                                 "ORDER BY originally_available_at DESC "
                                                 "LIMIT ?", (reference_date.isoformat().replace('T', ' '),
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

        if recent_releases_minimum-len(local_movie_list) > 0:
            for movieInfo in self.cursor.execute("SELECT id,title "  # ...but at least the last 3 movies
                                                 "FROM metadata_items "
                                                 "WHERE library_section_id = 1 "
                                                 "AND metadata_type = 1 "
                                                 "AND duration > 1 "
                                                 "AND originally_available_at < ? "
                                                 "ORDER BY originally_available_at DESC "
                                                 "LIMIT ?", (reference_date.isoformat().replace('T', ' '),
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

        return local_movie_list

    def old_but_gold(self, count=1):
        local_movie_list = list()
        for movie_info in self.cursor.execute("SELECT id,title "  # old but gold
                                              "FROM metadata_items "
                                              "WHERE id IN (SELECT id FROM metadata_items ORDER BY RANDOM()) "
                                              "AND originally_available_at < ? "
                                              "AND rating > 8 "
                                              "AND library_section_id = 1 "
                                              "AND metadata_type = 1 "
                                              "ORDER BY RANDOM() "
                                              "LIMIT ?", (datetime.now() + timedelta(days=+3652), count,)):

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

        return local_movie_list

    def hidden_gem(self, count=1):
        local_movie_list = list()

        lowest_popularity = 100000.0
        selected = -1
        for i in range(count):

            for movie_info in self.cursor.execute("SELECT id,title,year,rating "  # Potential hidden gem
                                                  "FROM metadata_items "
                                                  "WHERE id IN (SELECT id FROM metadata_items ORDER BY RANDOM()) "
                                                  "AND library_section_id = 1 "
                                                  "AND metadata_type = 1 "
                                                  "AND rating > 1 "
                                                  "ORDER BY RANDOM() "
                                                  "LIMIT 8"):
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
                    print("TMDB api failed, skipping one movie from the category 'Hidden Gems' see error:")
                    print("URL requested:" + e.geturl())
                    continue

                if data['total_results'] > 0:
                    compensated_pop = float(data['results'][0]['popularity']) * \
                                      (1.05 ** (2015 - int(year))) * \
                                      (1/(rating**1.2))
                    print(title, + compensated_pop)
                    if lowest_popularity > compensated_pop:
                        lowest_popularity = compensated_pop
                        selected = movie_id
                        print('.--^^^--.')

            if selected >= 0:
                local_movie_list.append(selected)

        return local_movie_list

    def random(self, count=1):
        local_movie_list = list()

        for row in self.cursor.execute("SELECT id,title  "  # Random
                                       "FROM metadata_items "
                                       "WHERE id IN (SELECT id FROM metadata_items ORDER BY RANDOM()) "
                                       "AND library_section_id = 1 "
                                       "AND metadata_type = 1 "
                                       "ORDER BY RANDOM() "
                                       "LIMIT ?", (count,)):

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

        return local_movie_list

    def commit(self, id_list):
        os.system("sudo service plexmediaserver stop")
        pos = 0
        timestamp = datetime.now().replace(microsecond=0) + timedelta(days=+1)
        for movie in id_list:
            now = timestamp + timedelta(seconds=-pos)
            self.cursor.execute("UPDATE metadata_items "
                                "SET added_at = ?"
                                "WHERE id = ?", (now.isoformat().replace('T', ' '), movie,))
            pos += 1
            self.db.commit()
            os.system("sudo service plexmediaserver start")

    @staticmethod
    def line_number():
        return inspect.currentframe().f_back.f_lineno





plex = PlexDatabaseEditor()
