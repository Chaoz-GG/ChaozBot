import datetime
import json

import mysql.connector

with open('config.json') as json_file:
    data = json.load(json_file)
    db_name = data['db_name']
    db_user = data['db_user']
    db_password = data['db_password']
    db_host = data['db_host']
    db_port = data['db_port']


# Fetch all the user IDs from the `users` table and check if the parsed ID is in the list or not
def already_exists(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select USER_ID from users;')

    for i in cursor:
        if user_id in i:
            cursor.close()
            db.close()

            return True

    return False


# Fetch all the user IDs from the `users_archive` table and check if the parsed ID is in the list or not
def archive_exists(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select USER_ID from users_archive;')

    for i in cursor:
        if user_id in i:
            cursor.close()
            db.close()

            return True

    return False


# Fetch all the users with the given region, favorite game and age requirements
def get_all_users(region: str = None, favorite_game: str = None, age: int = None):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    if region and favorite_game and age:
        # noinspection SqlDialectInspection, SqlNoDataSourceInspection
        cursor.execute('select USER_ID, STEAM_ID from users where REGION = %s and FAV_GAME = %s and '
                       'TIMESTAMPDIFF(YEAR, BIRTHDAY, CURDATE()) = %s;',
                       (region, favorite_game, age))

    elif region and favorite_game and not age:
        # noinspection SqlDialectInspection, SqlNoDataSourceInspection
        cursor.execute('select USER_ID, STEAM_ID from users where REGION = %s and FAV_GAME = %s;',
                       (region, favorite_game))

    elif favorite_game and age and not region:
        # noinspection SqlDialectInspection, SqlNoDataSourceInspection
        cursor.execute('select USER_ID, STEAM_ID from users where FAV_GAME = %s and '
                       'TIMESTAMPDIFF(YEAR, BIRTHDAY, CURDATE()) = %s;', (favorite_game, age))

    elif age and region and not favorite_game:
        # noinspection SqlDialectInspection, SqlNoDataSourceInspection
        cursor.execute('select USER_ID, STEAM_ID from users where TIMESTAMPDIFF(YEAR, BIRTHDAY, CURDATE()) = %s '
                       'and REGION = %s;', (age, region))

    elif region and not favorite_game and not age:
        # noinspection SqlDialectInspection, SqlNoDataSourceInspection
        cursor.execute('select USER_ID, STEAM_ID from users where REGION = %s;', (region,))

    elif favorite_game and not region and not age:
        # noinspection SqlDialectInspection, SqlNoDataSourceInspection
        cursor.execute('select USER_ID, STEAM_ID from users where FAV_GAME = %s;', (favorite_game,))

    elif age and not region and not favorite_game:
        # noinspection SqlDialectInspection, SqlNoDataSourceInspection
        cursor.execute('select USER_ID, STEAM_ID from users where TIMESTAMPDIFF(YEAR, BIRTHDAY, CURDATE()) = %s;',
                       (age,))

    else:
        # noinspection SqlDialectInspection, SqlNoDataSourceInspection
        cursor.execute('select USER_ID, STEAM_ID from users;')

    res = cursor.fetchall()

    cursor.close()
    db.close()

    return res


# Fetch the users whose birthday is today
def get_birthday_bois():
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select USER_ID from users WHERE DATE_FORMAT(BIRTHDAY,"%m-%d") = DATE_FORMAT(CURDATE(),"%m-%d");')

    res = cursor.fetchall()

    cursor.close()
    db.close()

    return res


# Fetch all the information about a user from the `users` table
def get_user(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select * from users where USER_ID = %s;', (user_id,))

    r = cursor.fetchone()

    cursor.close()
    db.close()

    res = {
        'user_id': r[0],
        'steam_id': r[1],
        'bio': r[2],
        'country': r[3],
        'region': r[4],
        'hours': r[5],
        'birthday': r[6],
        'timezone': r[7],
        'favorite_game': r[8]
    }

    return res


# Fetch the Steam ID of a user from their Discord ID
def get_steam_id(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select STEAM_ID from users where USER_ID = %s;', (user_id,))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


# Fetch the Discord ID of a user from their Steam ID
def get_user_id(steam_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select USER_ID from users where STEAM_ID = %s;', (steam_id,))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


# Fetch all the Steam IDs of all the users in the `users` table
def get_steam_ids():
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute(f'select STEAM_ID from users;')

    res = cursor.fetchall()

    for i in range(len(res)):
        res[i] = res[i][0]

    cursor.close()
    db.close()

    return res


# Check if a user has a generated verification token in the `authentication` table
def has_generated_token(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select USER_ID from authentication;')

    for i in cursor:
        if user_id in i:
            cursor.close()
            db.close()

            return True

    return False


# Insert the verification token for the user into the `authentication` table
def initiate_auth(user_id: int, token: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('insert into authentication (USER_ID, TOKEN) values(%s, %s);', (user_id, token))
    db.commit()

    cursor.close()
    db.close()


# Remove the authentication token for the user from the `authentication` table after successful verification
def cleanup_auth(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('delete from authentication where USER_ID = %s;', (user_id,))
    db.commit()

    cursor.close()
    db.close()


# Fetch the authentication token for a user from the `authentication` table
def get_token(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select TOKEN from authentication where USER_ID = %s;', (user_id,))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


# Insert a user to the `users` table
def add_user(user_id: int, steam_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('insert into users (USER_ID, STEAM_ID) values(%s, %s);', (user_id, steam_id))
    db.commit()

    cursor.close()
    db.close()


# Delete a user from the `users` table
def remove_user(user_id: int, steam_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('delete from users where USER_ID = %s;', (user_id,))

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('delete from mm_stats where STEAM_ID = %s;', (steam_id,))

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('delete from faceit_stats where STEAM_ID = %s;', (steam_id,))

    db.commit()

    cursor.close()
    db.close()


# Delete a user from the `users` table and insert their entry into the `users_archive` table
def archive_user(user_id: int, steam_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('insert into users_archive select * from users where USER_ID = %s;', (user_id,))

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('delete from users where USER_ID = %s;', (user_id,))

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('delete from mm_stats where STEAM_ID = %s;', (steam_id,))

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('delete from faceit_stats where STEAM_ID = %s;', (steam_id,))

    db.commit()

    cursor.close()
    db.close()


# Delete a user entry from the `users_archive` table
def unarchive_user(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('insert into users select * from users_archive where USER_ID = %s;', (user_id,))

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('delete from users_archive where USER_ID = %s;', (user_id,))

    db.commit()

    cursor.close()
    db.close()


# Fetch the user's bio from the `users` table
def get_bio(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select BIO from users where USER_ID = %s;', (user_id,))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


# Update the user's birthdate in the `users` table
def update_birthday(user_id: int, birthday: datetime.date):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update users SET BIRTHDAY = %s where USER_ID = %s;', (birthday, user_id))
    db.commit()

    cursor.close()
    db.close()


# Update the user's timezone in the `users` table
def update_timezone(user_id: int, timezone: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update users SET TIMEZONE = %s where USER_ID = %s;', (timezone, user_id))
    db.commit()

    cursor.close()
    db.close()


# Update the user's bio in the `users` table
def update_bio(user_id: int, bio: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update users SET BIO = %s where USER_ID = %s;', (bio, user_id))
    db.commit()

    cursor.close()
    db.close()


# Return the favorite games of the user from the `users` table as a list
def get_favorite_games(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('select FAVORITE_GAMES from users where USER_ID = %s;', (user_id,))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    if not res:
        return []

    else:
        return res.split('|')


# Update the user's favorite games in the `users` table
def update_favorite_games(user_id: int, favorite_game: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update users SET FAVORITE_GAMES = %s where USER_ID = %s;', (favorite_game, user_id))
    db.commit()

    cursor.close()
    db.close()


# Fetch the user's country name from the `users` table
def get_country(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select COUNTRY from users where USER_ID = %s;', (user_id,))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


# Update the user's country name in the `users` table
def update_country(user_id: int, country: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update users SET COUNTRY = %s where USER_ID = %s;', (country, user_id))
    db.commit()

    cursor.close()
    db.close()


# Fetch the user's region from the `users` table
def get_region(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select REGION from users where USER_ID = %s;', (user_id,))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


# Update the user's region in the `users` table
def update_region(user_id: int, region: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update users SET REGION = %s where USER_ID = %s;', (region, user_id))
    db.commit()

    cursor.close()
    db.close()


# Fetch the user's total playtime from the `users` table
def get_hours(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select HOURS from users where USER_ID = %s;', (user_id,))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


# Update the user's total playtime in the `users` table
def update_hours(user_id: int, hours: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update users SET HOURS = %s where USER_ID = %s;', (hours, user_id))
    db.commit()

    cursor.close()
    db.close()


# Fetch the region-wise leaderboard using optional matchmaking and FaceIT rank requirements
def sort_lb(region: str, mm_rank: str = None, faceit_rank: int = None):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    if mm_rank:
        # noinspection SqlDialectInspection,SqlNoDataSourceInspection
        cursor.execute('select users.STEAM_ID, users.USER_ID, mm_stats.RANK from mm_stats, users '
                       'where users.REGION = %s and mm_stats.RANK = %s and mm_stats.STEAM_ID = users.STEAM_ID '
                       'order by KPD desc;', (region, mm_rank))

    elif faceit_rank:
        # noinspection SqlDialectInspection,SqlNoDataSourceInspection
        cursor.execute('select users.STEAM_ID, users.USER_ID, faceit_stats.RANK from faceit_stats, users '
                       'where users.REGION = %s and faceit_stats.RANK = %s and faceit_stats.STEAM_ID = users.STEAM_ID '
                       'order by KPD desc;', (region, faceit_rank))

    else:
        # noinspection SqlDialectInspection,SqlNoDataSourceInspection
        cursor.execute('select users.STEAM_ID, users.USER_ID, mm_stats.RANK, faceit_stats.RANK from mm_stats, '
                       'faceit_stats, users where users.REGION = %s and mm_stats.STEAM_ID = users.STEAM_ID '
                       'and faceit_stats.STEAM_ID = users.STEAM_ID order by faceit_stats.RANK, '
                       'mm_stats.KPD, faceit_stats.KPD desc;',
                       (region,))

    res = cursor.fetchall()

    cursor.close()
    db.close()

    return res


# Fetch all the team names from the `teams` table
def get_all_team_names():
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select NAME from teams;')

    r = cursor.fetchall()

    res = []

    for i in r:
        res.append(i[0])

    cursor.close()
    db.close()

    return res


# Fetch all the team abbreviations from the `teams` table
def get_all_team_abbreviations():
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select ABBREVIATION from teams;')

    r = cursor.fetchall()

    res = []

    for i in r:
        res.append(i[0])

    cursor.close()
    db.close()

    return res


# Fetch the team ID, games and active game from the `teams` table
def get_all_teams_and_games():
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select TEAM_ID, GAMES, ACTIVE_GAME from teams;')

    r = cursor.fetchall()

    cursor.close()
    db.close()

    return r


# Insert a team into the `teams` table
def create_team(team_id: str, games: str, active_game: str, name: str, abbreviation: str, region: str,
                captain_steam_id: int, captain_discord_id: int, description: str = None, org_name: str = None):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('insert into teams (TEAM_ID, GAMES, ACTIVE_GAME, NAME, DESCRIPTION, ORG_NAME, ABBREVIATION, REGION, '
                   'CAPTAIN_STEAM_ID, CAPTAIN_DISCORD_ID) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);',
                   (team_id, games, active_game, name, description, org_name, abbreviation, region, captain_steam_id,
                    captain_discord_id))
    db.commit()

    cursor.close()
    db.close()


# Update the team's message ID in the `teams` table
def update_team_message_id(team_id: str, message_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set MESSAGE_ID = %s where TEAM_ID = %s;', (message_id, team_id))
    db.commit()

    cursor.close()
    db.close()


# Update the team's games in the `teams` table
def update_team_games(team_id: str, games: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set GAMES = %s where TEAM_ID = %s;', (games, team_id))
    db.commit()

    cursor.close()
    db.close()


# Update the team's active game in the `teams` table
def update_team_active_game(team_id: str, active_game: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set ACTIVE_GAME = %s where TEAM_ID = %s;', (active_game, team_id))
    db.commit()

    cursor.close()
    db.close()


# Update the team's region in the `teams` table
def update_team_region(team_id: str, region: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set REGION = %s where TEAM_ID = %s;', (region, team_id))
    db.commit()

    cursor.close()
    db.close()


# Update the team's description in the `teams` table
def update_team_description(team_id: str, description: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set DESCRIPTION = %s where TEAM_ID = %s;', (description, team_id))
    db.commit()

    cursor.close()
    db.close()


# Update the team's organization name in the `teams` table
def update_team_org_name(team_id: str, org_name: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set ORG_NAME = %s where TEAM_ID = %s;', (org_name, team_id))
    db.commit()

    cursor.close()
    db.close()


# Fetch all the information about a team from the `teams` table by team ID
def get_team_by_id(team_id: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select * from teams where TEAM_ID = %s;', (team_id,))

    r = cursor.fetchone()

    if not r:
        return False

    res = {
        'id': r[0],
        'games': r[1],
        'active_game': r[2],
        'name': r[3],
        'description': r[4],
        'org_name': r[5],
        'abbreviation': r[6],
        'region': r[7],
        'message_id': r[8],
        'captain_steam_id': r[9],
        'captain_discord_id': r[10],
        'members_steam_ids': r[11],
        'members_discord_ids': r[12],
        'substitutes_steam_ids': r[13],
        'substitutes_discord_ids': r[14]
    }

    cursor.close()
    db.close()

    return res


# Fetch all the information about a team from the `teams` table by message ID
def get_team_by_message_id(message_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select * from teams where MESSAGE_ID = %s;', (message_id,))

    r = cursor.fetchone()

    res = {
        'id': r[0],
        'games': r[1],
        'active_game': r[2],
        'name': r[3],
        'description': r[4],
        'org_name': r[5],
        'abbreviation': r[6],
        'region': r[7],
        'message_id': r[8],
        'captain_steam_id': r[9],
        'captain_discord_id': r[10],
        'members_steam_ids': r[11],
        'members_discord_ids': r[12],
        'substitutes_steam_ids': r[13],
        'substitutes_discord_ids': r[14]
    }

    cursor.close()
    db.close()

    return res


# Fetch all the information about a team from the `teams` table by captain's user ID
def get_teams_by_captain_id(captain_discord_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    if captain_discord_id == -1:
        # noinspection SqlDialectInspection, SqlNoDataSourceInspection
        cursor.execute('select TEAM_ID, NAME from teams;')

    else:
        # noinspection SqlDialectInspection, SqlNoDataSourceInspection
        cursor.execute('select TEAM_ID, NAME from teams where CAPTAIN_DISCORD_ID = %s;', (captain_discord_id,))

    r = cursor.fetchall()

    cursor.close()
    db.close()

    return r


# Fetch the member information about a team from the `teams` table by team ID
def get_team_members(team_id: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select MEMBERS_STEAM_IDS, MEMBERS_DISCORD_IDS from teams where TEAM_ID = %s;', (team_id,))

    r = cursor.fetchone()

    if r == (None, None):
        return {}

    member_steam_ids = r[0].split('|')
    member_discord_ids = r[1].split('|')

    member_data = dict(zip(member_steam_ids, member_discord_ids))

    if '' in member_data.keys():
        member_data.pop('')

    return member_data


# Fetch the substitute information about a team from the `teams` table by team ID
def get_team_substitutes(team_id: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select SUBSTITUTES_STEAM_IDS, SUBSTITUTES_DISCORD_IDS from teams where TEAM_ID = %s;', (team_id,))

    r = cursor.fetchone()

    if r == (None, None):
        return {}

    substitutes_steam_ids = r[0].split('|')
    substitutes_discord_ids = r[1].split('|')

    substitute_data = dict(zip(substitutes_steam_ids, substitutes_discord_ids))

    if '' in substitute_data.keys():
        substitute_data.pop('')

    return substitute_data


# Check if a team is full using the parsed maximum member count
def check_team_members_full(team_id: str, max_member_count: int):
    if max_member_count < 0:
        return False

    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select MEMBERS_STEAM_IDS from teams where TEAM_ID = %s;', (team_id,))

    r = cursor.fetchone()[0]

    return len(r.split('|')) >= max_member_count


# Check if a team is full using the parsed maximum substitute count
def check_team_subsitutes_full(team_id: str, max_substitute_count: int):
    if max_substitute_count < 0:
        return False

    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select SUBSTITUTES_STEAM_IDS from teams where TEAM_ID = %s;', (team_id,))

    r = cursor.fetchone()[0]

    return len(r.split('|')) >= max_substitute_count


# Check if the parsed steam ID is already a member in the team
def check_team_member_exists(team_id: str, member_steam_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select MEMBERS_STEAM_IDS from teams where TEAM_ID = %s;', (team_id,))

    r = cursor.fetchone()[0]

    return str(member_steam_id) in r.split('|')


# Check if the parsed steam ID is already a substitute in the team
def check_team_substitute_exists(team_id: str, substitute_steam_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select SUBSTITUTES_STEAM_IDS from teams where TEAM_ID = %s;', (team_id,))

    r = cursor.fetchone()[0]

    return str(substitute_steam_id) in r.split('|')


# Insert a member into a particular team ID in the `teams` table
def add_team_member(team_id: str, member_steam_id: int, member_discord_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    members = get_team_members(team_id)
    members[member_steam_id] = member_discord_id

    member_keys = [str(i) for i in list(members.keys())]
    member_values = [str(i) for i in list(members.values())]

    member_steam_ids = '|'.join(member_keys)
    member_discord_ids = '|'.join(member_values)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set MEMBERS_STEAM_IDS = %s where TEAM_ID = %s;', (member_steam_ids, team_id))
    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set MEMBERS_DISCORD_IDS = %s where TEAM_ID = %s;', (member_discord_ids, team_id))

    db.commit()

    cursor.close()
    db.close()


# Delete a member from a particular team ID in the `teams` table
def remove_team_member(team_id: str, member_steam_id: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    members = get_team_members(team_id)
    members.pop(member_steam_id)

    member_keys = [str(i) for i in list(members.keys())]
    member_values = [str(i) for i in list(members.values())]

    member_steam_ids = '|'.join(member_keys)
    member_discord_ids = '|'.join(member_values)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set MEMBERS_STEAM_IDS = %s where TEAM_ID = %s;', (member_steam_ids, team_id))
    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set MEMBERS_DISCORD_IDS = %s where TEAM_ID = %s;', (member_discord_ids, team_id))

    db.commit()

    cursor.close()
    db.close()


# Insert a substitute into a particular team ID in the `teams` table
def add_team_substitute(team_id: str, substitute_steam_id: int, substitute_discord_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    substitutes = get_team_substitutes(team_id)
    substitutes[substitute_steam_id] = substitute_discord_id

    substitute_keys = [str(i) for i in list(substitutes.keys())]
    substitute_values = [str(i) for i in list(substitutes.values())]

    substitute_steam_ids = '|'.join(substitute_keys)
    substitute_discord_ids = '|'.join(substitute_values)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set SUBSTITUTES_STEAM_IDS = %s where TEAM_ID = %s;', (substitute_steam_ids, team_id))
    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set SUBSTITUTES_DISCORD_IDS = %s where TEAM_ID = %s;',
                   (substitute_discord_ids, team_id))

    db.commit()

    cursor.close()
    db.close()


# Delete a substitute from a particular team ID in the `teams` table
def remove_team_substitute(team_id: str, substitute_steam_id: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    substitutes = get_team_substitutes(team_id)
    substitutes.pop(substitute_steam_id)

    substitute_keys = [str(i) for i in list(substitutes.keys())]
    substitute_values = [str(i) for i in list(substitutes.values())]

    substitute_steam_ids = '|'.join(substitute_keys)
    substitute_discord_ids = '|'.join(substitute_values)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set SUBSTITUTES_STEAM_IDS = %s where TEAM_ID = %s;', (substitute_steam_ids, team_id))
    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set SUBSTITUTES_DISCORD_IDS = %s where TEAM_ID = %s;',
                   (substitute_discord_ids, team_id))

    db.commit()

    cursor.close()
    db.close()


# Delete a team from the `teams` table
def remove_team(team_id: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('delete from teams where TEAM_ID = %s;', (team_id,))

    db.commit()

    cursor.close()
    db.close()


# Fetch all the requested members of a particular team from the `teams` table by team ID
def get_team_requested_members(team_id: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select REQUESTED_MEMBERS from teams where TEAM_ID = %s;', (team_id,))

    r = cursor.fetchone()[0]

    if not r:
        return []

    member_discord_ids = r.split('|')

    if '' in member_discord_ids:
        member_discord_ids.pop(member_discord_ids.index(''))

    return member_discord_ids


# Fetch all the requested substitutes of a particular team from the `teams` table by team ID
def get_team_requested_substitutes(team_id: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select REQUESTED_SUBSTITUTES from teams where TEAM_ID = %s;', (team_id,))

    r = cursor.fetchone()[0]

    if not r:
        return []

    substitutes_discord_ids = r.split('|')

    if '' in substitutes_discord_ids:
        substitutes_discord_ids.pop(substitutes_discord_ids.index(''))

    return substitutes_discord_ids


# Fetch all the blacklisted members of a particular team from the `teams` table by team ID
def get_team_blacklist(team_id: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select BLACKLIST from teams where TEAM_ID = %s;', (team_id,))

    r = cursor.fetchone()[0]

    if not r:
        return []

    blacklist_discord_ids = r.split('|')

    if '' in blacklist_discord_ids:
        blacklist_discord_ids.pop(blacklist_discord_ids.index(''))

    return blacklist_discord_ids


# Insert a member into the requested members of a particular team in the `teams` table by team ID
def add_team_requested_member(team_id: str, member_discord_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    members = get_team_requested_members(team_id)
    members.append(str(member_discord_id))

    member_discord_ids = '|'.join(members)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set REQUESTED_MEMBERS = %s where TEAM_ID = %s;', (member_discord_ids, team_id))

    db.commit()

    cursor.close()
    db.close()


# Delete a member from the requested members of a particular team in the `teams` table by team ID
def remove_team_requested_member(team_id: str, member_discord_id: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    members = get_team_requested_members(team_id)
    members.pop(members.index(str(member_discord_id)))

    member_discord_ids = '|'.join(members)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set REQUESTED_MEMBERS = %s where TEAM_ID = %s;', (member_discord_ids, team_id))

    db.commit()

    cursor.close()
    db.close()


# Insert a substitute into the requested substitutes of a particular team in the `teams` table by team ID
def add_team_requested_substitute(team_id: str, substitute_discord_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    substitutes = get_team_requested_substitutes(team_id)
    substitutes.append(str(substitute_discord_id))

    substitute_discord_ids = '|'.join(substitutes)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set REQUESTED_SUBSTITUTES = %s where TEAM_ID = %s;', (substitute_discord_ids, team_id))

    db.commit()

    cursor.close()
    db.close()


# Delete a substitute from the requested substitutes of a particular team in the `teams` table by team ID
def remove_team_requested_substitute(team_id: str, substitute_discord_id: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    substitutes = get_team_requested_substitutes(team_id)
    substitutes.pop(substitutes.index(str(substitute_discord_id)))

    substitute_discord_ids = '|'.join(substitutes)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set REQUESTED_SUBSTITUTES = %s where TEAM_ID = %s;', (substitute_discord_ids, team_id))

    db.commit()

    cursor.close()
    db.close()


# Insert a member into the blacklisted members of a particular team in the `teams` table by team ID
def add_team_blacklist(team_id: str, blacklist_discord_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    blacklists = get_team_blacklist(team_id)
    blacklists.append(str(blacklist_discord_id))

    blacklist_discord_ids = '|'.join(blacklists)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set BLACKLIST = %s where TEAM_ID = %s;', (blacklist_discord_ids, team_id))

    db.commit()

    cursor.close()
    db.close()


# Delete a member from the blacklisted members of a particular team in the `teams` table by team ID
def remove_team_blacklist(team_id: str, blacklist_discord_id: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    blacklists = get_team_blacklist(team_id)
    blacklists.pop(blacklists.index(str(blacklist_discord_id)))

    blacklist_discord_ids = '|'.join(blacklists)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update teams set BLACKLIST = %s where TEAM_ID = %s;', (blacklist_discord_ids, team_id))

    db.commit()

    cursor.close()
    db.close()
