import asyncio

import discord
from discord.ext import commands

import json
import logging
from datetime import datetime

from utils.core import load_cogs

from cogs.teams import Options, Create

with open('config.json') as json_file:
    data = json.load(json_file)
    token = data['bot_token']

# Export all dev log to log.txt file
logging.basicConfig(filename='log.txt',
                    filemode='a',
                    format='%(asctime)s - [%(levelname)s] %(message)s')  # , level=logging.INFO)


class ChaozBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set a common logger for both the library and the bot class
        self.log = logging.getLogger('ChaozBot')

    # Create persistent views
    async def setup_hook(self) -> None:
        self.add_view(Create())
        self.add_view(Options())


intents = discord.Intents.all()
# Command prefix is just a placeholder, since all our commands are slash commands
bot = ChaozBot(command_prefix='/', intents=intents)

# Store bot launch time for `ping` command
bot.launch_time = datetime.utcnow()

# Embed color for all the embeds used in the bot
bot.embed_colour = 0xffffff


async def main():
    async with bot:
        # Load all the cogs
        await load_cogs(bot)
        await bot.start(token)


# Create bot thread
asyncio.run(main())
