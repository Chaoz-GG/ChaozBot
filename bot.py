#!/usr/bin/python3

import discord
from discord.ext import commands

import json
import logging
from datetime import datetime

from utils.core import initialize_prefix, load_cogs

with open('config.json') as json_file:
    data = json.load(json_file)
    token = data['bot_token']

logging.basicConfig(format='%(asctime)s - [%(levelname)s] %(message)s', level=logging.INFO)


# noinspection PyMethodMayBeStatic
class ChaozBot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.log = logging.getLogger('FumeStop')


intents = discord.Intents.all()
bot = ChaozBot(command_prefix=initialize_prefix, case_insensitive=True, intents=intents)
bot.launch_time = datetime.utcnow()
bot.remove_command('help')

bot.emoji1 = '\u2705'
bot.emoji2 = '\u274C'

bot.embed_colour = 0xc29e29

if __name__ == '__main__':
    load_cogs(bot)
    bot.run(token)
