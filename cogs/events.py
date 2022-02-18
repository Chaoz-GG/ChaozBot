from discord.ext import commands, tasks

import json

import requests

from utils.db import get_steam_ids, get_steam_id, already_exists, remove_user


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open('config.json') as json_file:
            data = json.load(json_file)
            self.whitelist = data['whitelist']

    # Auto-update stats
    @tasks.loop(hours=12)
    async def _update_stats(self):
        for steam_id in get_steam_ids():
            requests.get(f'http://localhost:5000/stats/update/mm/{steam_id}')
            requests.get(f'http://localhost:5000/stats/update/faceit/{steam_id}')

    # Leave unexpected servers
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if guild.id not in self.whitelist:
            await guild.leave()

    # Erase member data on leaving
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if already_exists(member.id):
            steam_id = get_steam_id(member.id)

            remove_user(member.id, steam_id)


def setup(bot):
    bot.add_cog(Events(bot))
