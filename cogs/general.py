#!/usr/bin/python3

import math
import json
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from utils.db import count_users, get_all_users


with open('config.json') as json_file:
    data = json.load(json_file)
    whitelist = data['whitelist']
    sudo_role_ids = data['sudo_role_ids']


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='ping', description='Returns the API and bot latency.')
    @app_commands.guilds(whitelist)
    async def _ping(self, ctx: discord.Interaction):
        await ctx.response.defer(thinking=True)

        embed = discord.Embed(colour=self.bot.embed_colour)
        embed.description = '**Pong!**'

        ms = self.bot.latency * 1000

        embed.add_field(name='API latency (Heartbeat)', value=f'`{int(ms)} ms`')

        t1 = datetime.utcnow().strftime("%f")

        await ctx.edit_original_message(embed=embed)

        t2 = datetime.utcnow().strftime("%f")

        diff = int(math.fabs((int(t2) - int(t1)) / 1000))

        embed.add_field(name='Bot latency (Round-trip)', value=f'`{diff} ms`')

        await ctx.edit_original_message(embed=embed)

    @app_commands.command(name='view', description='View registered user list.')
    @app_commands.guilds(whitelist)
    async def _view(self, ctx: discord.Interaction):
        await ctx.response.defer(thinking=True)

        sudo_roles = []

        for sudo_role_id in sudo_role_ids:
            sudo_roles.append(ctx.guild.get_role(sudo_role_id))

        for sudo_role in sudo_roles:
            if sudo_role in ctx.user.roles:
                break

        else:
            return await ctx.edit_original_message(content='This is an administrator only command.')

        embed = discord.Embed(colour=self.bot.embed_colour)

        embed.title = 'Registered User List'
        embed.description = f'Total **{count_users()}** registered users\n\n'

        users = get_all_users()

        for user in enumerate(users):
            embed.description += f'`{user[0] + 1}.` {ctx.guild.get_member(user[1][0]).mention} - `{user[1][1]}`\n'

        await ctx.edit_original_message(embed=embed)


async def setup(bot):
    await bot.add_cog(General(bot))
