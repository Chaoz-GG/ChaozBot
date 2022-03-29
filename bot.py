import asyncio

import discord
from discord.ext import commands

import json
import logging
from datetime import datetime

from utils.core import load_cogs

with open('config.json') as json_file:
    data = json.load(json_file)
    token = data['bot_token']

logging.basicConfig(filename='log.txt',
                    filemode='a',
                    format='%(asctime)s - [%(levelname)s] %(message)s')  # , level=logging.INFO)


class ChaozBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.log = logging.getLogger('ChaozBot')


intents = discord.Intents.all()
bot = ChaozBot(command_prefix='/', intents=intents)

bot.launch_time = datetime.utcnow()

bot.embed_colour = 0xffffff


async def main():
    async with bot:
        await load_cogs(bot)
        await bot.start(token)


asyncio.run(main())
