#!/usr/bin/python3

import json

import discord
from discord import app_commands
from discord.ext import commands


with open('config.json') as json_file:
    data = json.load(json_file)
    whitelist = data['whitelist']


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='help', description='Help command!')
    @app_commands.guilds(whitelist)
    async def _help(self, ctx: discord.Interaction):
        await ctx.response.defer(thinking=True)

        embed = discord.Embed(colour=self.bot.embed_colour)

        embed.title = 'Commands'

        embed.add_field(name='General',
                        value=f'`ping`',
                        inline=False)

        embed.add_field(name='Profile',
                        value=f'`steam`, `link`, `unlink`, `bio`, `country`',
                        inline=False)

        embed.add_field(name='Statistics',
                        value=f'`mmstats`, `faceitstats`, `update`',
                        inline=False)

        await ctx.edit_original_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
