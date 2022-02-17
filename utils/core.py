#!/usr/bin/python3

from discord.ext import commands

import os
import json


with open('config.json') as json_file:
    data = json.load(json_file)
    prefix = data['prefix']


def load_cogs(bot):
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename[:-3]}')


def initialize_prefix(bot, message):
    return commands.when_mentioned_or(prefix)(bot, message)
