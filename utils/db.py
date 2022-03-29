#!/usr/bin/python3

import json

import mysql.connector

with open('config.json') as json_file:
    data = json.load(json_file)
    db_name = data['db_name']
    db_user = data['db_user']
    db_password = data['db_password']
    db_host = data['db_host']
    db_port = data['db_port']


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


def get_steam_id(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select STEAM_ID from users where USER_ID = %s;', (user_id, ))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


def get_user_id(steam_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select USER_ID from users where STEAM_ID = %s;', (steam_id, ))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


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


def initiate_auth(user_id: int, token: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('insert into authentication (USER_ID, TOKEN) values(%s, %s);', (user_id, token))
    db.commit()

    cursor.close()
    db.close()


def cleanup_auth(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('delete from authentication where USER_ID = %s;', (user_id, ))
    db.commit()

    cursor.close()
    db.close()


def get_token(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select TOKEN from authentication where USER_ID = %s;', (user_id, ))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


def add_user(user_id: int, steam_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('insert into users (USER_ID, STEAM_ID) values(%s, %s);', (user_id, steam_id))
    db.commit()

    cursor.close()
    db.close()


def remove_user(user_id: int, steam_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('delete from users where USER_ID = %s;', (user_id, ))

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('delete from mm_stats where STEAM_ID = %s;', (steam_id, ))

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('delete from faceit_stats where STEAM_ID = %s;', (steam_id, ))

    db.commit()

    cursor.close()
    db.close()


def get_bio(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select BIO from users where USER_ID = %s;', (user_id, ))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


def update_bio(user_id: int, bio: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update users SET BIO = %s where USER_ID = %s;', (bio, user_id))
    db.commit()

    cursor.close()
    db.close()


def get_country(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select COUNTRY from users where USER_ID = %s;', (user_id, ))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


def update_country(user_id: int, country: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update users SET COUNTRY = %s where USER_ID = %s;', (country, user_id))
    db.commit()

    cursor.close()
    db.close()


def get_region(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select REGION from users where USER_ID = %s;', (user_id, ))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


def update_region(user_id: int, region: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update users SET REGION = %s where USER_ID = %s;', (region, user_id))
    db.commit()

    cursor.close()
    db.close()


def get_hours(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select HOURS from users where USER_ID = %s;', (user_id, ))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


def update_hours(user_id: int, hours: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update users SET HOURS = %s where USER_ID = %s;', (hours, user_id))
    db.commit()

    cursor.close()
    db.close()


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
                       'and faceit_stats.STEAM_ID = users.STEAM_ID order by  mm_stats.KPD, faceit_stats.KPD desc;',
                       (region, ))

    res = cursor.fetchall()

    cursor.close()
    db.close()

    return res
