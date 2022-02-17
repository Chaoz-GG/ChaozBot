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
    cursor.execute('select USER_ID from Users;')

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
    cursor.execute('select STEAM_ID from Users where USER_ID = %s;', (user_id, ))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


def get_steam_ids():
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute(f'select STEAM_ID from Statistics;')

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
    cursor.execute('select USER_ID from Authentication;')

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
    cursor.execute('insert into Authentication (USER_ID, TOKEN) values(%s, %s);', (user_id, token))
    db.commit()

    cursor.close()
    db.close()


def cleanup_auth(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('delete from Authentication where USER_ID = %s;', (user_id, ))
    db.commit()

    cursor.close()
    db.close()


def get_token(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select TOKEN from Authentication where USER_ID = %s;', (user_id, ))

    res = cursor.fetchone()

    cursor.close()
    db.close()

    return res


def add_user(user_id: int, steam_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('insert into Users (USER_ID, STEAM_ID) values(%s, %s);', (user_id, steam_id))
    db.commit()

    cursor.close()
    db.close()


def remove_user(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('delete from Users where USER_ID = {user_id};', (user_id, ))
    db.commit()

    cursor.close()
    db.close()


def get_bio(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select BIO from Users where USER_ID = %s;', (user_id, ))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


def update_bio(user_id: int, bio: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update Users SET BIO = %s where USER_ID = %s;', (bio, user_id))
    db.commit()

    cursor.close()
    db.close()


def get_country(user_id: int):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection, SqlNoDataSourceInspection
    cursor.execute('select COUNTRY from Users where USER_ID = %s;', (user_id, ))

    res = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return res


def update_country(user_id: int, country: str):
    db = mysql.connector.connect(host=db_host, port=db_port, user=db_user,
                                 passwd=db_password, database=db_name)
    cursor = db.cursor(buffered=True)

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    cursor.execute('update Users SET COUNTRY = %s where USER_ID = %s;', (country, user_id))
    db.commit()

    cursor.close()
    db.close()
