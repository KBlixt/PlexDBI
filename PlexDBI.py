try:
    import sys
    import sqlite3
    from datetime import datetime
    from datetime import timedelta
    import json
    import urllib.request
    import urllib.error
    import configparser
    import inspect
    import time
    import os
    from collections import OrderedDict
    from sys import platform as _platform
except ImportError:
    print('-------------------------------------------------------------------')
    print('Unable to import one or more modules.')
    print('Make sure that you are running the script with an updated python 3.')
    print('-------------------------------------------------------------------')
    sys.exit()


class PlexMoviesDBI:
    def __init__(self, cursor, config_file):
        self.cursor = cursor
        self.local_movie_list = dict()
        self.movies_provided = 0

        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        try:
            self.library_section = int(self.config.get('REQUIRED', 'MOVIE_LIBRARY_SECTION'))
            self.tmdb_api_key = self.config.get('OPTIONAL', 'TMDB_API_KEY')

            self.recent_releases_minimum_count = int(self.config.get('RECENT_RELEASES', 'MIN_COUNT'))
            self.recent_releases_maximum_count = int(self.config.get('RECENT_RELEASES', 'MAX_COUNT'))
            self.recent_releases_order = int(self.config.get('RECENT_RELEASES', 'ORDER'))
            self.recent_releases_day_limit = int(self.config.get('RECENT_RELEASES', 'DAY_LIMIT'))

            self.old_but_gold_count = int(self.config.get('OLD_BUT_GOLD', 'COUNT'))
            self.old_but_gold_order = int(self.config.get('OLD_BUT_GOLD', 'ORDER'))
            self.old_but_gold_year_limit = int(self.config.get('OLD_BUT_GOLD', 'YEAR_LIMIT'))
            self.old_but_gold_min_critic_score = float(self.config.get('OLD_BUT_GOLD', 'MIN_CRITIC_SCORE'))

            self.hidden_gem_count = int(self.config.get('HIDDEN_GEM', 'COUNT'))
            self.hidden_gem_order = int(self.config.get('HIDDEN_GEM', 'ORDER'))

            self.random_count = int(self.config.get('RANDOM', 'COUNT'))
            self.random_order = int(self.config.get('RANDOM', 'ORDER'))
            if self.recent_releases_minimum_count < 0:
                self.recent_releases_minimum_count = 0
            if self.recent_releases_minimum_count > self.recent_releases_maximum_count:
                self.recent_releases_minimum_count = self.recent_releases_maximum_count
            if self.old_but_gold_count < 0:
                self.old_but_gold_count = 0
            if self.hidden_gem_count < 0:
                self.hidden_gem_count = 0
            if self.random_count < 0:
                self.random_count = 0

        except ValueError:
            print('---------------------------------------------------------------------------')
            print('Something seems to be wrong in the config file.')
            print('Make sure that everything in the "REQUIRED" section is filled out correctly.')
            print('All the parameters expects a number except for the TMDB_API_KEY parameter.')
            print('---------------------------------------------------------------------------')
            raise ValueError
        except configparser.NoSectionError:
            print('---------------------------------------------------------------------------')
            print('Something seems to be wrong with the config file.')
            print('To fix this you could let the script generate a new config file and refill ')
            print('the config file. Or if the script isn\'t producing a config file as expected')
            print('you can fill in the empty one and rename it to "config".')
            print('---------------------------------------------------------------------------')
            raise ValueError

        if not self.check_library_section(self.library_section):
            raise ValueError

        self.order_power = max(self.recent_releases_maximum_count,
                               self.random_count,
                               self.hidden_gem_count,
                               self.old_but_gold_count)
        self.compress_order()

    def compress_order(self):

        order_list = {'recent_releases': self.recent_releases_order,
                      'old_but_gold': self.old_but_gold_order,
                      'hidden_gem': self.hidden_gem_order,
                      'random_order': self.random_order}

        order_list = OrderedDict(sorted(order_list.items(), key=lambda t: t[1]))

        pos = 0
        for i in order_list:
            order_list[i] = pos
            pos += 1

        self.recent_releases_order = order_list['recent_releases']
        self.old_but_gold_order = order_list['old_but_gold']
        self.hidden_gem_order = order_list['hidden_gem']
        self.random_order = order_list['random_order']

    def find_movies(self):
        self.recent_releases(self.recent_releases_minimum_count,
                             self.recent_releases_maximum_count,
                             self.recent_releases_order,
                             self.recent_releases_day_limit)

        self.old_but_gold(self.old_but_gold_count,
                          self.old_but_gold_order,
                          self.old_but_gold_year_limit,
                          self.old_but_gold_min_critic_score)

        if self.tmdb_api_key != '':
            self.hidden_gem(self.hidden_gem_count,
                            self.hidden_gem_order)
        else:
            print("INFO: You have not specified a tmdb api key.")

        self.random(self.random_count,
                    self.random_order)

        return self.local_movie_list

    def check_library_section(self, library_section):
        self.cursor.execute("SELECT language,section_type "
                            "FROM library_sections "
                            "WHERE id = ?", (library_section,))

        info = self.cursor.fetchone()

        try:

            if info[0] == 'xn' or info[1] != 1:
                print('Your MOVIE_LIBRARY_SECTION parameter in the config file is not a Movie library.')
                print('These libraries are movie libraries and can be used in this script:')
                print('-----------------------------------------------------------------------------------------')

                for library in self.cursor.execute("SELECT id, name "
                                                   "FROM library_sections "
                                                   "WHERE language IS NOT 'xn' "
                                                   "AND section_type = 1 "
                                                   "ORDER BY id ASC "):
                    print('The library "' + library[1] + '" have section_id: ' + str(library[0]) + '.')

                print('-----------------------------------------------------------------------------------------')
                print('Please use one of these ID\'s as your MOVIE_LIBRARY_SECTION parameter in the config file.')

                return False
        except TypeError:
            print('Your MOVIE_LIBRARY_SECTION parameter in the config file is not a Movie library.')
            print('These libraries are movie libraries and can be used in this script:')
            print('-----------------------------------------------------------------------------------------')

            for library in self.cursor.execute("SELECT id, name "
                                               "FROM library_sections "
                                               "WHERE language IS NOT 'xn' "
                                               "AND section_type = 1 "
                                               "ORDER BY id ASC "):
                print('The library "' + library[1] + '" have section_id: ' + str(library[0]) + '.')

            print('-----------------------------------------------------------------------------------------')
            print('Please use one of these ID\'s as your MOVIE_LIBRARY_SECTION parameter in the config file.')

            return False
        return True

    def get_reference_date(self):
        try:
            self.cursor.execute("SELECT originally_available_at "  # most recent movie for reference
                                "FROM metadata_items "
                                "WHERE library_section_id = ? "
                                "AND metadata_type = 1 "
                                "AND duration > 1 "
                                "ORDER BY originally_available_at DESC ", (self.library_section,))
        except sqlite3.OperationalError:
            print('------------------------------------------------------------------')
            print('Remember to fill in the MOVIE_LIBRARY_SECTION in the config file. ')
            print('Also make sure that the "PlexDatabase.db" syslink isn\'t broken. ')
            print('here is a list on viable libraries you have: ')
            print('------------------------------------------------------------------')
            print('Exiting')

            return "error"

        for attempt in self.cursor.fetchall():
            reference_date = attempt[0]
            if reference_date != 'None':
                reference_date = reference_date
                return reference_date

        print("----Script failed----")
        print("Failed finding a reference date.")
        return "error"

    def recent_releases(self, minimum, maximum, order, day_limit):
        self.movies_provided = 0
        if PlexMoviesDBI.get_reference_date(self) == 'error':
            return
        else:
            reference_date = datetime.strptime(PlexMoviesDBI.get_reference_date(self), '%Y-%m-%d %H:%M:%S') \
                             + timedelta(days=-day_limit)

        if maximum > 0:
            for movieInfo in self.cursor.execute("SELECT id,title "  # modifies 7 movies within 14 days...
                                                 "FROM metadata_items "
                                                 "WHERE library_section_id = ? "
                                                 "AND metadata_type = 1 "
                                                 "AND duration > 1 "
                                                 "AND originally_available_at > ? "
                                                 "ORDER BY originally_available_at DESC "
                                                 "LIMIT ?", (self.library_section,
                                                             reference_date.isoformat().replace('T', ' '),
                                                             maximum)):

                movie_id = movieInfo[0]
                title = str(movieInfo[1])

                if title == 'None':
                    print("----Script failed----")
                    print("No title were found for a movie and it was skipped.")
                    print("Not a critical error and can be ignored unless it's a common occurrence.")
                    print("movie_id: " + movie_id)
                    continue
                elif movie_id == 'None':
                    print("----Script failed----")
                    print("No id were found for a movie and it was skipped.")
                    print("Not a critical error and can be ignored unless it's a common occurrence.")
                    continue

                self.add_to_queue(movie_id, order, title)
        if minimum - len(self.local_movie_list) > 0:
            for movieInfo in self.cursor.execute("SELECT id,title "  # ...but at least the last 3 movies
                                                 "FROM metadata_items "
                                                 "WHERE library_section_id = ? "
                                                 "AND metadata_type = 1 "
                                                 "AND duration > 1 "
                                                 "AND originally_available_at < ? "
                                                 "ORDER BY originally_available_at DESC "
                                                 "LIMIT ?", (self.library_section,
                                                             reference_date.isoformat().replace('T', ' '),
                                                             minimum - len(self.local_movie_list),)):

                movie_id = movieInfo[0]
                title = str(movieInfo[1])

                if title == 'None':
                    print("----Script failed----")
                    print("No title were found for a movie and it was skipped.")
                    print("Not a critical error and can be ignored unless it's a common occurrence.")
                    print("movie_id: " + movie_id)
                    continue
                elif movie_id == 'None':
                    print("----Script failed----")
                    print("No id were found for a movie and it was skipped.")
                    print("Not a critical error and can be ignored unless it's a common occurrence.")
                    continue

                self.add_to_queue(movie_id, order, title)

    def old_but_gold(self, count, order, age_limit, score_limit):
        self.movies_provided = 0
        for movie_info in self.cursor.execute("SELECT id,title "  # old but gold
                                              "FROM metadata_items "
                                              "WHERE id IN (SELECT id FROM metadata_items ORDER BY RANDOM()) "
                                              "AND originally_available_at < ? "
                                              "AND rating > ? "
                                              "AND library_section_id = ? "
                                              "AND metadata_type = 1 "
                                              "ORDER BY RANDOM() "
                                              "LIMIT ?", (datetime.now() + timedelta(days=-(age_limit*365)),
                                                          score_limit,
                                                          self.library_section, count,)):

            movie_id = movie_info[0]
            title = str(movie_info[1])

            if title == 'None':
                print("----Script failed----")
                print("No title were found for a movie and it was skipped.")
                print("Not a critical error and can be ignored unless it's a common occurrence.")
                print("movieId: " + movie_id)
                continue
            elif movie_id == 'None':
                print("----Script failed----")
                print("No id were found for a movie and it was skipped.")
                print("Not a critical error and can be ignored unless it's a common occurrence.")
                continue

            self.add_to_queue(movie_id, order, title)

    def hidden_gem(self, count, order):
        self.movies_provided = 0

        for i in range(count):
            lowest_popularity = 100000.0
            selected_id = -1
            selected_title = ''

            for movie_info in self.cursor.execute("SELECT id,title,year,rating "  # Potential hidden gem
                                                  "FROM metadata_items "
                                                  "WHERE id IN (SELECT id FROM metadata_items ORDER BY RANDOM()) "
                                                  "AND library_section_id = ? "
                                                  "AND metadata_type = 1 "
                                                  "AND rating > 1 "
                                                  "ORDER BY RANDOM() "
                                                  "LIMIT 8", (self.library_section,)):
                movie_id = movie_info[0]
                title = str(movie_info[1])
                year = str(movie_info[2])
                rating = movie_info[3]

                if title == 'None':
                    print("----Script failed----")
                    print("No title were found for a movie and it was skipped.")
                    print("Not a critical error and can be ignored unless it's a common occurrence.")
                    print("movie_id: " + movie_id)
                    print("year: " + year)
                    print("rating: " + rating)
                    continue
                elif movie_id == 'None':
                    print("----Script failed----")
                    print("No id were found for the movie \"" + title + "\" and it was skipped.")
                    print("Not a critical error and can be ignored unless it's a common occurrence.")
                    continue
                elif year == 'None':
                    print("----Script failed----")
                    print("No year were found for the movie \"" + title + "\" and it was skipped.")
                    print("Not a critical error and can be ignored unless it's a common occurrence.")
                    continue

                title = title.replace(' ', '+')
                title = title.encode('ascii', errors='ignore')  # sanitise title from unicode characters
                title = title.decode('utf-8')

                try:

                    response = urllib.request.urlopen('https://api.themoviedb.org/3/search/movie'
                                                      '?api_key=' + self.tmdb_api_key +
                                                      '&query=' + title +
                                                      '&year=' + year)
                    data = json.loads(response.read().decode('utf-8'))

                except urllib.error.HTTPError as urlib_error:
                    print("----Script failed----")
                    print("TMDB api failed, skipping one movie from the category 'Hidden Gems' see error: ")
                    print("URL requested: " + urlib_error.geturl())
                    print("Reason: " + urlib_error.reason)
                    continue

                if data['total_results'] > 0:
                    compensated_pop = float(data['results'][0]['popularity']) * \
                                      (1.05 ** (2015 - int(year))) * \
                                      (1 / (rating ** 1.2))
                    if lowest_popularity > compensated_pop:
                        lowest_popularity = compensated_pop
                        selected_id = movie_id
                        selected_title = title

            if selected_id >= 0:
                self.add_to_queue(selected_id, order, selected_title.replace('+', ' '))

    def random(self, count, order):
        self.movies_provided = 0

        for row in self.cursor.execute("SELECT id,title  "  # Random
                                       "FROM metadata_items "
                                       "WHERE id IN (SELECT id FROM metadata_items ORDER BY RANDOM()) "
                                       "AND library_section_id = ? "
                                       "AND metadata_type = 1 "
                                       "ORDER BY RANDOM() "
                                       "LIMIT ?", (self.library_section, count,)):

            movie_id = row[0]
            title = str(row[1])

            if title == 'None':
                print("----Script failed----")
                print("No title were found for a movie and it was skipped.")
                print("Not a critical error and can be ignored unless it's a common occurrence.")
                print("movie_id: " + movie_id)
                continue
            if movie_id == 'None':
                print("----Script failed----")
                print("No id were found for the movie \"" + title + "\" and it was skipped.")
                print("Not a critical error and can be ignored unless it's a common occurrence.")
                continue

            self.add_to_queue(movie_id, order, title)

    def add_to_queue(self, movie_id, order, title):
        self.local_movie_list[movie_id] = self.movies_provided + order * self.order_power
        self.movies_provided += 1
        print('Adding item to movie queue. Title:  "' + title + '"')


class PlexDBI:
    def __init__(self, operative_system, root_access, database_file, config_file):
        self.os = operative_system
        self.root_access = root_access
        self.operative_system = operative_system
        if not os.path.isfile(config_file):
            self.generate_config(config_file)

        if not os.path.isfile(database_file):
            self.symlink_database(database_file)
        self.database = sqlite3.connect(database_file)
        self.cursor = self.database.cursor()

        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        try:
            movies = PlexMoviesDBI(self.cursor, config_file)
            mod_queue = movies.find_movies()
            self.commit(mod_queue)
        except ValueError:
            raise ValueError

        self.database.close()

    def commit(self, mod_queue):
        if self.config.get('OPTIONAL', 'BACKUP') == 'yes':
            if op_system == 'linux':
                if self.root_access:
                    print('--Stopping plexmediaserver.')
                    os.system("sudo service plexmediaserver stop")
            elif op_system == 'windows':
                print('--Stopping plexmediaserver.')
                os.system('taskkill /F /IM "Plex Media Server.exe" /T')
            elif op_system == 'mac_os':
                os.system('killall "Plex Media Server"')

        print('----Processing movie queue.')
        timestamp = datetime.now().replace(microsecond=0) + timedelta(days=+1)
        for movie_id in mod_queue:
            now = timestamp + timedelta(seconds=-mod_queue[movie_id])
            self.cursor.execute("UPDATE metadata_items "
                                "SET added_at = ?"
                                "WHERE id = ?", (now.isoformat().replace('T', ' '), movie_id,))

        print('----Movie queue processed, committing to db.')
        self.database.commit()
        print('----Changes committed.')
        if op_system == 'linux':
                if self.root_access:
                    print('--Starting plexmediaserver.')
                    os.system("sudo service plexmediaserver start")
                else:
                    print('You can now proceed to restart your Plex server.')
        elif op_system == 'windows':
            print('--Starting plexmediaserver.')
            os.system('start /B "C:\Program Files\Plex Media Server\Plex Media Server.exe"')
            os.system('start /B "C:\Program Files (x86)\Plex Media Server\Plex Media Server.exe"')
            print("")
        elif op_system == 'mac_os':
            print('--Starting plexmediaserver.')
            os.system('open /Applications/Plex\ Media\ Server.app')
        else:
            print('You can now proceed to restart your Plex server.')

    def symlink_database(self, database_file):
        if op_system == 'linux':
            if self.root_access:
                os.system('ln -s "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/'
                          'Plug-in Support/Databases/com.plexapp.plugins.library.db" "'
                          + os.getcwd() + '/' + database_file + '"')
        elif op_system == 'windows':
            os.system('mklink %LOCALAPPDATA%\Plex Media Server\Plug-in Support\Databases\com.plexapp.plugins.library.db'
                      ' "' + os.getcwd() + '/' + database_file + '"')
        elif op_system == 'mac_os':
            os.system('ln -s ~/Library/Application Support/Plex Media Server/Plug-in Support/Databases/'
                      'com.plexapp.plugins.library.db'
                      ' "' + os.getcwd() + '/' + database_file + '"')
        else:
            pass

    def generate_config(self, config_file_name):
        f = open(config_file_name, "w+")

        if self.operative_system == 'linux':
            os.system("sudo chown --reference=" + os.getcwd() + "/PlexDBI.py " + config_file_name)

        f.write('')
        f.write('\n[REQUIRED]')
        f.write('\n    MOVIE_LIBRARY_SECTION = 0')
        f.write('\n')
        f.write('\n[OPTIONAL]')
        f.write('\n    # leave blank if you don\'t have a key.')
        f.write('\n    TMDB_API_KEY = ')
        f.write('\n    # Do you want to make a copy of your database before modifying it? (yes/no)')
        f.write('\n    BACKUP = yes')
        f.write('\n')
        f.write('\n[MOVIES_SETTINGS]')
        f.write('\n    # Here you can control the settings for each individual category')
        f.write('\n    # the "COUNT" parameter specifies how manny movies from each category will be modified')
        f.write('\n    # and the "ORDER" specifies in what order the categories will appear.')
        f.write('\n')
        f.write('\n    # The [RECENT_RELEASES] category will provide a list of movies with the most recent releases')
        f.write('\n    # that isn\'t older than the[DAY_LIMIT].')
        f.write('\n    # At least [MIN_COUNT] and at the most [MAX_COUNT] will be provided.')
        f.write('\n    [RECENT_RELEASES]')
        f.write('\n        MIN_COUNT = 3')
        f.write('\n        MAX_COUNT = 7')
        f.write('\n        ORDER = 1')
        f.write('\n        DAY_LIMIT = 14')
        f.write('\n')
        f.write('\n    # The [OLD_BUT_GOLD] category will provide a random list of movies')
        f.write('\n    # that is at least [YEAR_LIMIT] old')
        f.write('\n    # years old but with a minimum critic score of [CRITIC_SCORE] (in a scale from 0 to 10)')
        f.write('\n    [OLD_BUT_GOLD]')
        f.write('\n        COUNT = 1')
        f.write('\n        ORDER = 2')
        f.write('\n        YEAR_LIMIT = 10')
        f.write('\n        MIN_CRITIC_SCORE = 7.9')
        f.write('\n    # The [HIDDEN_GEM] category will provide a random list of movies')
        f.write('\n    # that have a low popularity on TMDB.')
        f.write('\n    # Note that this category requires an TMDB_API_KEY to be used.')
        f.write('\n    [HIDDEN_GEM]')
        f.write('\n        COUNT = 1')
        f.write('\n        ORDER = 3')
        f.write('\n    # The [RANDOM] category will provide a list of random movies.')
        f.write('\n    [RANDOM]')
        f.write('\n        COUNT = 1')
        f.write('\n        ORDER = 4')
        f.write('\n')
        f.close()

    @staticmethod
    def backup_database():
        if op_system == 'linux':
            os.system('cp PlexDatabase.db PlexDatabase.backup.db')
        elif op_system == 'mac_os':
            os.system('cp PlexDatabase.db PlexDatabase.backup.db')
        elif op_system == 'windows':
            os.system('copy PlexDatabase.db PlexDatabase.backup.db')


start = time.time()


if _platform == "linux" or _platform == "linux2":
    op_system = 'linux'
elif _platform == "darwin":
    op_system = 'mac_os'
elif _platform == "win32" or _platform == "win64":
    op_system = 'windows'
else:
    op_system = 'unknown'
    print("---------------------------------------------------------------------------------------------------------")
    print("You are not running this script on a Linux, Windows or mac OS, I'm not sure how this will effect")
    print("this script. But anything that requires to input or output to the system will excluded when running this")
    print("script. It mostly need that capability when setting up files. So if you make sure you have the ")
    print("database and the config file in place the rest should run smoothly")
    print("---------------------------------------------------------------------------------------------------------")
if op_system == 'linux':

    try:
        has_root_access = 0 == os.getuid()
    except AttributeError as e:
        print(e.args)
        has_root_access = False
elif op_system == 'windows' or op_system == 'mac_os':
    has_root_access = True
else:
    has_root_access = False


try:
    modify_plex_server_1 = PlexDBI(op_system, has_root_access, 'PlexDatabase.db', 'config')
except ValueError:
    pass
end = time.time()

print("----End of script----")
print("Script completed in " + str(int(end - start)) + " seconds.")
