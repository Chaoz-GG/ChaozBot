import discord
from discord.ext import commands

import json

from utils.db import get_steam_id, already_exists, remove_user


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open('config.json') as json_file:
            data = json.load(json_file)
            self.whitelist = data['whitelist']

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync(guild=discord.Object(id=self.whitelist))

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


async def setup(bot):
    await bot.add_cog(Events(bot))
