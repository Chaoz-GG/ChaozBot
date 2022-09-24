import math
import json
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from utils.tools import log_message


with open('config.json') as json_file:
    data = json.load(json_file)
    whitelist = data['whitelist']

    chaoz_logo_url = data['chaoz_logo_url']


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='ping', description='Returns the API and bot latency.')
    @app_commands.guilds(whitelist)
    async def _ping(self, ctx: discord.Interaction):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        embed = discord.Embed(colour=self.bot.embed_colour)

        embed.set_thumbnail(url=chaoz_logo_url)

        embed.title = 'Pong!'

        # Obtain the gateway latency
        ms = self.bot.latency * 1000

        embed.add_field(name='API latency (Heartbeat)', value=f'`{int(ms)} ms`')

        t1 = datetime.utcnow().strftime("%f")

        await ctx.edit_original_response(embed=embed)

        t2 = datetime.utcnow().strftime("%f")

        # Calculate the round trip latency
        diff = int(math.fabs((int(t2) - int(t1)) / 1000))

        embed.add_field(name='Bot latency (Round-trip)', value=f'`{diff} ms`')

        await ctx.edit_original_response(embed=embed)


async def setup(bot):
    await bot.add_cog(General(bot))
