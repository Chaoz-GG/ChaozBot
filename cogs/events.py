from discord.ext import commands, tasks

import requests

from utils.db import get_steam_ids


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(hours=12)
    async def _update_stats(self):
        for steam_id in get_steam_ids():
            requests.get(f'http://localhost:5000/stats/update/mm/{steam_id}')
            requests.get(f'http://localhost:5000/stats/update/faceit/{steam_id}')


def setup(bot):
    bot.add_cog(Events(bot))
